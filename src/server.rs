//! Minimal HTTP API over a node.

use std::sync::Arc;
use std::sync::atomic::Ordering::Relaxed;

use axum::extract::{Path, Query, State};
use axum::http::StatusCode;
use axum::routing::{get, post};
use axum::{Json, Router};
use serde::Deserialize;
use serde_json::{Value as Json_, json};

use crate::node::Node;
use crate::state::Proc;

#[derive(Deserialize)]
struct ReadParams {
    #[serde(default)]
    min_seq: u64,
    #[serde(default)]
    prefix: String,
    limit: Option<usize>,
}

pub fn router(node: Arc<Node>) -> Router {
    Router::new()
        .route("/txn", post(txn))
        .route("/get/{key}", get(get_key))
        .route("/scan", get(scan))
        .route("/status", get(status))
        .with_state(node)
}

async fn txn(State(node): State<Arc<Node>>, Json(proc): Json<Proc>) -> (StatusCode, Json<Json_>) {
    match node.submit(proc).await {
        Ok(r) => (StatusCode::OK, Json(json!(r))),
        Err(e) => (StatusCode::SERVICE_UNAVAILABLE, Json(json!({ "error": format!("{e:#}") }))),
    }
}

async fn get_key(State(node): State<Arc<Node>>, Path(key): Path<String>, Query(p): Query<ReadParams>) -> Json<Json_> {
    let (seq, value) = node.get(&key, p.min_seq).await;
    Json(json!({ "seq": seq, "key": key, "value": value }))
}

async fn scan(State(node): State<Arc<Node>>, Query(p): Query<ReadParams>) -> Json<Json_> {
    let (seq, items) = node.scan(&p.prefix, p.limit.unwrap_or(100), p.min_seq).await;
    Json(json!({ "seq": seq, "items": items }))
}

async fn status(State(node): State<Arc<Node>>) -> Json<Json_> {
    let (next_seq, keys, txns, hash) = node.with_state(|s| (s.next_seq, s.kv.len(), s.txns_applied, s.hash()));
    let st = &node.stats;
    Json(json!({
        "node": format!("{:016x}", node.id),
        "next_seq": next_seq,
        "keys": keys,
        "txns_applied": txns,
        "state_hash": format!("{hash:016x}"),
        "epochs_written": st.epochs.load(Relaxed),
        "append_conflicts": st.conflicts.load(Relaxed),
    }))
}
