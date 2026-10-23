//! The shared log: the only durable state and the only coordination point.

use std::sync::Mutex;
use std::time::Duration;

use async_trait::async_trait;
use bytes::Bytes;
use tokio::sync::Notify;
use tokio::time::{Instant, sleep, timeout_at};

#[derive(Debug, Clone)]
pub struct Record {
    pub seq: u64,
    pub body: Bytes,
}

#[derive(Debug)]
pub enum AppendError {
    /// The log's tail was not at the expected position; nothing was appended.
    Mismatch { tail: u64 },
    /// Unknown outcome: the record may or may not have been appended.
    Other(anyhow::Error),
}

#[async_trait]
pub trait Log: Send + Sync + 'static {
    /// Appends `body` as one record, iff the log's tail is `expected` when given.
    /// Returns the record's sequence number.
    async fn append(&self, expected: Option<u64>, body: Bytes) -> Result<u64, AppendError>;

    /// Reads records from `from` on. At the tail, waits up to `wait` for new records,
    /// returning an empty batch if none arrive.
    async fn read(&self, from: u64, wait: Duration) -> anyhow::Result<Vec<Record>>;
}

/// In-process log with simulated round-trip latency and lost acknowledgements.
pub struct MemLog {
    records: Mutex<Vec<Bytes>>,
    appended: Notify,
    latency: Duration,
    /// Probability that a successful append reports an error anyway.
    lost_ack: f64,
}

impl MemLog {
    pub fn new(latency: Duration, lost_ack: f64) -> Self {
        Self { records: Mutex::new(Vec::new()), appended: Notify::new(), latency, lost_ack }
    }
}

#[async_trait]
impl Log for MemLog {
    async fn append(&self, expected: Option<u64>, body: Bytes) -> Result<u64, AppendError> {
        sleep(self.latency / 2).await;
        let result = {
            let mut records = self.records.lock().unwrap();
            let tail = records.len() as u64;
            if expected.is_none_or(|e| e == tail) {
                records.push(body);
                Ok(tail)
            } else {
                Err(AppendError::Mismatch { tail })
            }
        };
        self.appended.notify_waiters();
        sleep(self.latency / 2).await;
        if result.is_ok() && rand::random::<f64>() < self.lost_ack {
            return Err(AppendError::Other(anyhow::anyhow!("simulated lost ack")));
        }
        result
    }

    async fn read(&self, from: u64, wait: Duration) -> anyhow::Result<Vec<Record>> {
        let deadline = Instant::now() + wait;
        sleep(self.latency / 2).await;
        loop {
            let notified = self.appended.notified();
            tokio::pin!(notified);
            notified.as_mut().enable();
            let batch: Vec<Record> = {
                let records = self.records.lock().unwrap();
                let end = records.len().min(from as usize + 1000);
                (from as usize..end).map(|i| Record { seq: i as u64, body: records[i].clone() }).collect()
            };
            if !batch.is_empty() {
                sleep(self.latency / 2).await;
                return Ok(batch);
            }
            if timeout_at(deadline, notified).await.is_err() {
                return Ok(Vec::new());
            }
        }
    }
}
