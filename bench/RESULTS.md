# Results

## S2 Express, from laptop (2026-10-23)

Basin `logdb-bench-976641`, `aws:us-west-2`, storage class express (3-AZ quorum of S3 Express buckets), 1-day retention. Client: laptop, ~30 ms TCP RTT to us-west-2. Raw data: `results/s2-20261023-134057-1627ad.json`.

| Test | p50 | p99 |
|---|---|---|
| Tail read (≈ 1 RTT) | 30.5 ms | 36.6 ms |
| Append 256 B | 60.5 ms | 102 ms |
| Append 4 KiB | 60.9 ms | 114 ms |
| Append 64 KiB | 65.4 ms | 95 ms |
| Append 512 KiB | 108 ms | 131 ms |

- **Commit service time ≈ 30 ms** (append p50 minus tail-read p50). Estimate; confirm from EC2 in us-west-2.
- **One sequential writer: 15 appends/s** from laptop. Bounded by RTT + commit time, not S2.
- 4 writers: 53.5 ops/s; 16 writers: 158 ops/s at 9.9 MiB/s. The 16-writer run likely hit laptop uplink (512 KiB appends imply ~85 Mbit/s).
- **Race: 100/100 rounds had exactly one winner** across 8 writers; losers got `412 seq_num_mismatch`. Losers wait as long as winners.

Implications for design 1:
- S2 Express is multi-AZ, which removes the single-zone risk of raw S3 Express.
- Unary conditional appends cap one sequencer at ~1/(RTT + 30 ms): ~25–30 epochs/s in-region. Shorter epochs need pipelined appends over an append session (S2 limit: 200 batches/s per stream).
