# log-db

A prototype database whose only durable state is a shared log (currently [S2](https://s2.dev)). No WAL tier, no consensus cluster, no replication protocol.

- Transactions are stored procedures (`put`, `delete`, `incr`, `transfer`).
- A node batches submitted transactions into an epoch and commits it with one append. The log records transaction inputs, not effects.
- Every node applies the log in order. Execution is deterministic, so every node reaches the same state and computes the same outcomes. A replica is any node that reads the log.
- Any number of nodes can write. `--append conditional` appends only at the tail the node has applied up to and retries at the reported tail on a lost race; `--append unconditional` lets the log order appends and needs no races.
- Each batch carries its writer's ID and a batch number. Appends with an unknown outcome are retried; every node skips a batch number it has already applied.
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

`bench/scripts/writers.sh 15 2000 --append <mode> --log s2 --basin logdb-bench-976641`: 2,000 clients spread over 1–10 writer nodes, 1 replica, laptop → S2. Full tables, both epoch waits and the in-memory log: [bench/results/writers-s2.md](bench/results/writers-s2.md), [bench/results/writers-mem.md](bench/results/writers-mem.md). Epoch wait 0 below.

| writers | conditional txn/s | p50 ms | p99 ms | lost races/epoch | unconditional txn/s | p50 ms | p99 ms | epochs/s |
|---|---|---|---|---|---|---|---|---|
| 1 | 27,811 | 70.2 | 150.9 | 0 | 26,167 | 68.7 | 340.9 | 13.5 |
| 2 | 12,121 | 164.3 | 380.4 | 0.97 | 23,379 | 74.2 | 188.5 | 23.6 |
| 4 | 7,421 | 238.9 | 604.6 | 2.58 | 18,443 | 113.0 | 300.6 | 37.6 |
| 6 | 5,504 | 255.7 | 1,698.2 | 4.71 | 15,786 | 132.0 | 319.9 | 48.6 |
| 8 | 4,129 | 312.1 | 2,189.4 | 6.70 | 12,566 | 159.4 | 389.3 | 51.1 |
| 10 | 3,364 | 413.2 | 3,965.6 | 8.50 | 8,917 | 187.2 | 814.8 | 45.3 |

All 48 runs (S2 and in-memory): every node identical, money conserved. With 10% of in-memory acknowledgements dropped (`--mem-lost-acks 0.1`), retried batches landed twice and every node skipped the same duplicates.

- **Conditional:** the log commits a fixed ~15 epochs/s however many nodes write. Each epoch costs about writers − 1 lost races; p99 reaches 4 s at 10 writers.
- **Unconditional:** no races. Epochs/s grows with writers up to ~50/s, then flattens; on the in-memory log it keeps growing (165/s at 10 writers). The S2 ceiling is unexplained from the laptop: S2 under concurrent appends, the 10 in-process nodes each downloading every epoch, or the laptop link.
- **Latency floor is two round trips** with several writers: the append, then reading the other writers' records that landed before it. One writer needs only the append.
- Throughput still falls with writers because each writer batches only its own clients; total clients stay at 2,000.

## Not yet

- Pipelined appends (S2 append sessions); currently one append in flight per node.
- Checkpoints: nodes replay the whole log on start.
- S3 Express backend.
- Runs from EC2 in-region.
