# log-db

A prototype database whose only durable state is a shared log with conditional append (currently [S2](https://s2.dev)). No WAL tier, no consensus cluster, no replication protocol.

- Transactions are stored procedures (`put`, `delete`, `incr`, `transfer`).
- A node batches submitted transactions into an epoch and commits it with one conditional append: append only if the log's tail is where the node expects.
- Every node applies the log in order. Execution is deterministic, so every node reaches the same state. A replica is any node that reads the log.
- Any number of nodes can write. A node that loses an append race retries at the tail reported by the log, then catches up.
- Queries run against the node's in-memory state. Passing `min_seq` waits until the node has applied that far (read-your-writes across nodes).

Background and design rationale: [docs/research.md](docs/research.md). Log benchmarks: [bench/](bench/).

## Run

`.env` holds `S2_API_KEY`; set `S2_BASIN` there or pass `--basin`.

```bash
cargo build --release
```

In-process benchmark (bank transfers; verifies all nodes end identical and money is conserved):

```bash
./target/release/logdb bench                                  # in-memory log, 30 ms simulated RTT
./target/release/logdb bench --log s2 --basin logdb-bench-976641 --clients 2000
./target/release/logdb bench --log s2 --basin logdb-bench-976641 --writers 2 --replicas 2
```

HTTP node (run several on the same `--stream`):

```bash
./target/release/logdb serve --log s2 --basin logdb-bench-976641 --stream demo --listen 127.0.0.1:7000
curl -XPOST localhost:7000/txn -H 'content-type: application/json' -d '{"op":"put","key":"bal/1","value":100}'
curl -XPOST localhost:7000/txn -H 'content-type: application/json' -d '{"op":"transfer","from":"bal/1","to":"bal/2","amount":30}'
curl 'localhost:7000/scan?prefix=bal/&min_seq=2'
curl localhost:7000/get/bal%2F1
curl localhost:7000/status
```

## First numbers (laptop → S2 Express us-west-2, ~30 ms RTT)

| Setup | Throughput | p50 | p99 |
|---|---|---|---|
| 1 writer, 2,000 clients | 23.5k txn/s | 82 ms | 150 ms |
| 1 writer, 10,000 clients | 51k txn/s | 171 ms | 360 ms |
| 2 writers, 2,000 clients | 11k txn/s | 171 ms | 359 ms |

All runs: replicas identical to writers, money conserved.

- One log commits ~12 epochs/s from the laptop (one append in flight at a time). Throughput comes from batch size: up to ~10k transfers per epoch.
- The 10k-client run is bound by laptop upload (750 KB epochs).
- Multiple writers add latency, not throughput: they alternate epochs and nearly every epoch costs one lost race.

Epoch wait (`--epoch-ms`, default 0): with 0, a node sends whatever queued during the previous append as soon as it returns. Against a 5 ms wait, 0 gives ~5 ms lower p50 and 5–15% more throughput. With 2,000 closed-loop clients its p99 can be worse: stragglers miss a wave and form a small epoch of their own. On S2 from the laptop the difference is within run-to-run noise.

| Log, clients | `--epoch-ms` | Throughput | p50 | p99 |
|---|---|---|---|---|
| mem 30 ms, 100 | 0 | 2,882 txn/s | 34.6 ms | 41.2 ms |
| mem 30 ms, 100 | 5 | 2,480 txn/s | 40.5 ms | 42.4 ms |
| mem 30 ms, 2,000 | 0 | 50,704 txn/s | 38.9 ms | 73.2 ms |
| mem 30 ms, 2,000 | 5 | 44,000 txn/s | 45.4 ms | 52.7 ms |
| S2, 100 (2 runs) | 0 | 1,629 / 1,520 txn/s | 60.3 / 62.0 ms | 86 / 157 ms |
| S2, 100 (2 runs) | 5 | 1,470 / 1,440 txn/s | 65.7 / 65.6 ms | 164 / 220 ms |
| S2, 2,000 (2 runs) | 0 | 24,081 / 26,117 txn/s | 77.2 / 73.3 ms | 157 / 145 ms |
| S2, 2,000 (2 runs) | 5 | 24,700 / 25,800 txn/s | 79.4 / 77.7 ms | 142 / 120 ms |

## Multiple writers

`bench/scripts/writers.sh 15 2000 --log s2 --basin logdb-bench-976641`: 2,000 clients spread over 1–10 writer nodes, 1 replica. Laptop → S2.

| writers | epoch ms | txn/s | p50 ms | p99 ms | max ms | epochs/s | txns/epoch | conflicts/epoch |
|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 25,637 | 74.9 | 148.5 | 191.5 | 13.1 | 1962 | 0.00 |
| 1 | 5 | 23,733 | 82.1 | 173.6 | 205.3 | 11.9 | 2000 | 0.00 |
| 2 | 0 | 10,189 | 181.8 | 743.2 | 1849.6 | 10.3 | 986 | 0.92 |
| 2 | 5 | 11,733 | 168.3 | 296.6 | 311.5 | 11.7 | 1000 | 0.99 |
| 4 | 0 | 7,646 | 193.0 | 1148.9 | 1963.1 | 15.5 | 492 | 2.89 |
| 4 | 5 | 8,100 | 199.3 | 721.2 | 822.1 | 16.2 | 500 | 2.70 |
| 6 | 0 | 4,363 | 301.9 | 3434.9 | 4658.4 | 13.2 | 331 | 4.72 |
| 6 | 5 | 5,223 | 232.5 | 2052.7 | 2628.8 | 15.7 | 333 | 4.60 |
| 8 | 0 | 3,826 | 373.0 | 3537.5 | 3782.9 | 15.9 | 241 | 6.68 |
| 8 | 5 | 4,000 | 331.9 | 2352.6 | 3438.1 | 16.0 | 250 | 6.47 |
| 10 | 0 | 3,159 | 371.8 | 5592.9 | 12678.4 | 16.0 | 197 | 8.63 |
| 10 | 5 | 3,307 | 292.4 | 5702.4 | 9047.6 | 16.5 | 200 | 8.54 |

All runs: every node identical, money conserved. The in-memory log (30 ms) shows the same shape at about twice the rates.

- The log commits a fixed number of epochs per second regardless of writer count. Each writer only batches its own clients, so throughput falls roughly as 1/writers.
- Each epoch costs about writers − 1 lost races. Unlucky writers lose many in a row: p99 reaches 5.6 s at 10 writers.
- A 5 ms epoch wait helps with several writers (tighter tails); with one writer, 0 is better.

## Not yet

- Pipelined appends (S2 append sessions); currently one append in flight per node.
- Checkpoints: nodes replay the whole log on start.
- S3 Express backend.
- Runs from EC2 in-region.
