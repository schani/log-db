# logbench

Conditional-append latency, throughput and race safety on S3 Express One Zone and S2.

Tests:
- **latency**: sequential conditional appends per payload size, plus tail-read baseline.
- **throughput**: N independent writers, each appending sequentially to its own log for `--seconds`.
- **race**: `--race-writers` clients append at the same position each round; exactly one must win and the tail must advance by exactly one append. Round 0 races object/stream creation.

Results go to `results/<backend>-<run>.json`.

## Run where it counts

S3 Express is zonal. Run from an EC2 instance in the bucket's AZ ID (the harness records the client's AZ). Laptop runs measure the internet path, not the service.

## S3 Express

```bash
./logbench.py s3x --bucket logbench--use1-az4--x-s3 --region us-east-1
```

Needs a directory bucket and `s3express:CreateSession` permission. Each append object is limited to 10,000 appends; the harness rolls to a new segment before that.

## S2

```bash
set -a; . ../.env; set +a   # S2_API_KEY
./logbench.py s2 --basin logdb-bench-976641
```

Streams are created as `<stream-prefix>-<run>-<name>`. If creation fails, enable create-on-append for the basin.

## Smoke test

```bash
./logbench.py mem --n 200 --seconds 2 --race-rounds 50
```
