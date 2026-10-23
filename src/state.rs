//! Transactions and the deterministic state machine that executes them.
//!
//! Transactions are stored procedures: a closed set of operations, each a pure function of
//! the current state. Every node executes the same log in the same order, so every node
//! reaches the same state without coordinating.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};
use xxhash_rust::xxh3::Xxh3;

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
#[serde(untagged)]
pub enum Value {
    Int(i64),
    Text(String),
}

#[derive(Serialize, Deserialize, Clone, Debug)]
#[serde(tag = "op", rename_all = "snake_case")]
pub enum Proc {
    Put { key: String, value: Value },
    Delete { key: String },
    Incr { key: String, by: i64 },
    /// Moves `amount` between integer keys; aborts if `from` would go negative.
    Transfer { from: String, to: String, amount: i64 },
}

/// One epoch: the unit appended to the log.
#[derive(Serialize, Deserialize)]
pub struct Batch {
    pub writer: u64,
    pub txns: Vec<Proc>,
}

impl Batch {
    pub fn encode(&self) -> Vec<u8> {
        rmp_serde::to_vec_named(self).expect("batch encodes")
    }

    pub fn decode(bytes: &[u8]) -> Option<Self> {
        rmp_serde::from_slice(bytes).ok()
    }
}

#[derive(Serialize, Clone, Debug, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum Outcome {
    Committed,
    Aborted(String),
}

#[derive(Default)]
pub struct State {
    pub kv: BTreeMap<String, Value>,
    /// Sequence number of the next log record to apply.
    pub next_seq: u64,
    pub txns_applied: u64,
}

impl State {
    /// Applies one log record. Undecodable records are skipped, deterministically.
    pub fn apply(&mut self, seq: u64, body: &[u8]) -> Vec<Outcome> {
        assert_eq!(seq, self.next_seq, "records must be applied in order");
        self.next_seq = seq + 1;
        let Some(batch) = Batch::decode(body) else {
            tracing::warn!(seq, "skipping undecodable record");
            return Vec::new();
        };
        self.txns_applied += batch.txns.len() as u64;
        batch.txns.iter().map(|p| self.execute(p)).collect()
    }

    fn execute(&mut self, proc: &Proc) -> Outcome {
        match proc {
            Proc::Put { key, value } => {
                self.kv.insert(key.clone(), value.clone());
            }
            Proc::Delete { key } => {
                self.kv.remove(key);
            }
            Proc::Incr { key, by } => {
                let Some(cur) = self.int(key) else { return Outcome::Aborted(format!("{key} is not an integer")) };
                self.kv.insert(key.clone(), Value::Int(cur + by));
            }
            Proc::Transfer { from, to, amount } => {
                let (Some(a), Some(b)) = (self.int(from), self.int(to)) else {
                    return Outcome::Aborted("transfer between non-integers".into());
                };
                if *amount < 0 || a < *amount {
                    return Outcome::Aborted("insufficient funds".into());
                }
                if from != to {
                    self.kv.insert(from.clone(), Value::Int(a - amount));
                    self.kv.insert(to.clone(), Value::Int(b + amount));
                }
            }
        }
        Outcome::Committed
    }

    /// Missing keys read as 0.
    fn int(&self, key: &str) -> Option<i64> {
        match self.kv.get(key) {
            None => Some(0),
            Some(Value::Int(i)) => Some(*i),
            Some(Value::Text(_)) => None,
        }
    }

    /// Digest of the full state; equal across nodes at the same `next_seq`.
    pub fn hash(&self) -> u64 {
        let mut h = Xxh3::new();
        h.update(&self.next_seq.to_le_bytes());
        for (k, v) in &self.kv {
            h.update(&(k.len() as u64).to_le_bytes());
            h.update(k.as_bytes());
            match v {
                Value::Int(i) => {
                    h.update(&[0]);
                    h.update(&i.to_le_bytes());
                }
                Value::Text(s) => {
                    h.update(&[1]);
                    h.update(&(s.len() as u64).to_le_bytes());
                    h.update(s.as_bytes());
                }
            }
        }
        h.digest()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn batch_roundtrip() {
        let b = Batch {
            writer: 7,
            txns: vec![
                Proc::Put { key: "a".into(), value: Value::Int(5) },
                Proc::Put { key: "b".into(), value: Value::Text("hi".into()) },
                Proc::Transfer { from: "a".into(), to: "c".into(), amount: 2 },
            ],
        };
        let mut s = State::default();
        let out = s.apply(0, &b.encode());
        assert_eq!(out, vec![Outcome::Committed; 3]);
        assert_eq!(s.kv["a"], Value::Int(3));
        assert_eq!(s.kv["c"], Value::Int(2));
        assert_eq!(s.kv["b"], Value::Text("hi".into()));
    }

    #[test]
    fn transfer_aborts_on_insufficient_funds() {
        let b = Batch { writer: 1, txns: vec![Proc::Transfer { from: "a".into(), to: "b".into(), amount: 1 }] };
        let mut s = State::default();
        assert!(matches!(s.apply(0, &b.encode())[0], Outcome::Aborted(_)));
    }
}
