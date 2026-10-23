#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["boto3>=1.36", "httpx>=0.27"]
# ///
"""Benchmark conditional-append latency and throughput on S3 Express One Zone and S2.

Every append is conditional: it succeeds only if the log is at the expected
position (S3 Express: byte offset via x-amz-write-offset-bytes; S2: record
sequence number via match_seq_num). This is the commit primitive for a
deterministic epoch log: one append per epoch, fenced by position.
"""

import argparse
import base64
import json
import os
import platform
import socket
import threading
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import NamedTuple

KiB = 1024


class AppendResult(NamedTuple):
    ok: bool
    next_pos: int | None
    error: str | None


# --- backends -----------------------------------------------------------------


class MemLog:
    """In-process log with simulated round-trip latency, for testing the harness."""

    def __init__(self, latency_ms: float, state: dict | None = None):
        self.latency = latency_ms / 1000
        self.state = state or {"pos": 0, "lock": threading.Lock()}
        self.needs_roll = False

    def append_if(self, expected: int, payload: bytes) -> AppendResult:
        time.sleep(self.latency / 2)
        with self.state["lock"]:
            pos = self.state["pos"]
            if pos != expected:
                result = AppendResult(False, pos, "Mismatch")
            else:
                self.state["pos"] = pos + 1
                result = AppendResult(True, pos + 1, None)
        time.sleep(self.latency / 2)
        return result

    def tail(self) -> int:
        time.sleep(self.latency)
        with self.state["lock"]:
            return self.state["pos"]

    def roll(self) -> int:
        return self.tail()

    def clone(self) -> "MemLog":
        return MemLog(self.latency * 1000, self.state)


class S3ExpressLog:
    """A log stored as appendable objects in an S3 Express One Zone directory bucket.

    Position is the byte offset in the current segment object. An object accepts at
    most 10,000 appends, so the log rolls to a new segment before hitting that.
    """

    MAX_PARTS = 10_000
    ROLL_AT = MAX_PARTS - 10

    def __init__(self, bucket: str, region: str, prefix: str, client=None):
        self.bucket, self.region, self.prefix = bucket, region, prefix
        self.client = client or self._make_client(region)
        self.segment = 0
        self.parts = 0

    @staticmethod
    def _make_client(region: str):
        import boto3
        from botocore.config import Config

        return boto3.client(
            "s3",
            region_name=region,
            config=Config(retries={"max_attempts": 1, "mode": "standard"}, tcp_keepalive=True),
        )

    @property
    def key(self) -> str:
        return f"{self.prefix}/seg-{self.segment:06d}"

    @property
    def needs_roll(self) -> bool:
        return self.parts >= self.ROLL_AT

    def append_if(self, expected: int, payload: bytes) -> AppendResult:
        from botocore.exceptions import ClientError

        try:
            # Offset 0 creates the object if it does not exist.
            self.client.put_object(Bucket=self.bucket, Key=self.key, Body=payload, WriteOffsetBytes=expected)
        except ClientError as e:
            err = e.response.get("Error", {})
            status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            return AppendResult(False, None, f"{status}:{err.get('Code')}")
        self.parts += 1
        return AppendResult(True, expected + len(payload), None)

    def tail(self) -> int:
        from botocore.exceptions import ClientError

        try:
            return self.client.head_object(Bucket=self.bucket, Key=self.key)["ContentLength"]
        except ClientError as e:
            if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                return 0
            raise

    def roll(self) -> int:
        self.segment += 1
        self.parts = 0
        return 0

    def clone(self) -> "S3ExpressLog":
        log = S3ExpressLog(self.bucket, self.region, self.prefix)
        log.segment, log.parts = self.segment, self.parts
        return log


class S2Log:
    """An S2 stream. Position is the record sequence number; one record per append."""

    def __init__(self, basin: str, stream: str, token: str):
        import httpx

        self.basin, self.stream, self.token = basin, stream, token
        self.base = f"https://{basin}.b.s2.dev/v1"
        self.http = httpx.Client(headers={"Authorization": f"Bearer {token}"}, timeout=30)
        self.needs_roll = False

    def ensure_stream(self) -> None:
        r = self.http.post(f"{self.base}/streams", json={"stream": self.stream})
        if r.status_code not in (200, 201, 409):
            print(f"warning: could not create stream {self.stream!r}: HTTP {r.status_code} {r.text[:200]}")

    def append_if(self, expected: int, payload: bytes) -> AppendResult:
        body = {"records": [{"body": base64.b64encode(payload).decode()}], "match_seq_num": expected}
        r = self.http.post(f"{self.base}/streams/{self.stream}/records", json=body, headers={"s2-format": "base64"})
        if r.status_code == 200:
            return AppendResult(True, r.json()["end"]["seq_num"], None)
        if r.status_code == 412:
            info = r.json()
            return AppendResult(False, info.get("seq_num_mismatch"), "412:" + ",".join(info))
        return AppendResult(False, None, f"{r.status_code}:{r.text[:100]}")

    def tail(self) -> int:
        r = self.http.get(f"{self.base}/streams/{self.stream}/records/tail")
        r.raise_for_status()
        return r.json()["tail"]["seq_num"]

    def roll(self) -> int:
        return self.tail()

    def clone(self) -> "S2Log":
        return S2Log(self.basin, self.stream, self.token)


def log_factory(args, run_id: str):
    """Returns make_log(name) creating an independent log per name."""
    if args.backend == "mem":
        return lambda name: MemLog(args.mem_latency_ms)
    if args.backend == "s3x":
        return lambda name: S3ExpressLog(args.bucket, args.region, f"{args.prefix}/{run_id}/{name}")

    token = os.environ["S2_API_KEY"]

    def make_s2(name: str) -> S2Log:
        log = S2Log(args.basin, f"{args.stream_prefix}-{run_id}-{name}", token)
        log.ensure_stream()
        return log

    return make_s2


# --- measurement ----------------------------------------------------------------


def summarize(ms: list[float]) -> dict:
    if not ms:
        return {"count": 0}
    s = sorted(ms)

    def pct(p: float) -> float:
        return round(s[min(len(s) - 1, int(p * len(s)))], 3)

    return {
        "count": len(s),
        "mean": round(sum(s) / len(s), 3),
        "min": round(s[0], 3),
        "p50": pct(0.50),
        "p90": pct(0.90),
        "p99": pct(0.99),
        "p999": pct(0.999),
        "max": round(s[-1], 3),
    }


def timed_ms(fn, *a):
    t0 = time.perf_counter_ns()
    r = fn(*a)
    return r, (time.perf_counter_ns() - t0) / 1e6


def append_loop(log, payload: bytes, *, count: int | None = None, until: float | None = None) -> list[float]:
    """Sequential conditional appends from the log's current tail. Returns latencies in ms."""
    pos = log.tail()
    lats = []
    while (count is None or len(lats) < count) and (until is None or time.perf_counter() < until):
        if log.needs_roll:
            pos = log.roll()
        r, ms = timed_ms(log.append_if, pos, payload)
        if not r.ok:
            raise RuntimeError(f"unexpected conditional-append failure at {pos}: {r.error}")
        pos = r.next_pos
        lats.append(ms)
    return lats


def run_latency(make_log, sizes: list[int], n: int, warmup: int) -> dict:
    log = make_log("latency")
    out = {}
    for size in sizes:
        payload = os.urandom(size)
        lats = append_loop(log, payload, count=warmup + n)[warmup:]
        out[f"append_{size}B"] = summarize(lats)
        print(f"  append {size:>8} B  {fmt(out[f'append_{size}B'])}")
    reads = [timed_ms(log.tail)[1] for _ in range(n)]
    out["tail_read"] = summarize(reads)
    print(f"  tail read          {fmt(out['tail_read'])}")
    return out


def run_throughput(make_log, size: int, seconds: float, parallel: int) -> dict:
    """`parallel` writers, each appending sequentially to its own log."""
    logs = [make_log(f"tp{parallel}-{i}") for i in range(parallel)]
    payload = os.urandom(size)
    results: list[list[float] | Exception] = [[] for _ in range(parallel)]
    barrier = threading.Barrier(parallel)

    def worker(i: int) -> None:
        barrier.wait()
        try:
            results[i] = append_loop(logs[i], payload, until=time.perf_counter() + seconds)
        except Exception as e:  # noqa: BLE001 - report per-writer failure
            results[i] = e

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(parallel)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    errors = [repr(r) for r in results if isinstance(r, Exception)]
    lats = [ms for r in results if isinstance(r, list) for ms in r]
    per_writer = [len(r) / seconds for r in results if isinstance(r, list)]
    out = {
        "payload_bytes": size,
        "seconds": seconds,
        "writers": parallel,
        "total_ops_per_s": round(len(lats) / seconds, 1),
        "total_MiB_per_s": round(len(lats) * size / seconds / KiB / KiB, 2),
        "per_writer_ops_per_s": summarize(per_writer),
        "latency_ms": summarize(lats),
        "errors": errors,
    }
    print(
        f"  {parallel:>3} writer(s) x {size} B: {out['total_ops_per_s']} ops/s, "
        f"{out['total_MiB_per_s']} MiB/s; latency {fmt(out['latency_ms'])}"
        + (f"; {len(errors)} writer error(s): {errors[0]}" if errors else "")
    )
    return out


def run_race(make_log, writers: int, rounds: int, size: int) -> dict:
    """`writers` clients append at the same expected position; exactly one must win."""
    base = make_log("race")
    clients = [base.clone() for _ in range(writers)]
    pos = base.tail()
    winners_hist: Counter = Counter()
    error_codes: Counter = Counter()
    win_ms, lose_ms, integrity_violations = [], [], []

    for rnd in range(rounds):
        barrier = threading.Barrier(writers)
        res: list = [None] * writers

        def worker(i: int, at: int = pos, rnd: int = rnd) -> None:
            payload = f"w{i} r{rnd} ".encode().ljust(size, b".")
            barrier.wait()
            res[i] = timed_ms(clients[i].append_if, at, payload)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(writers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        winners = 0
        for r, ms in res:
            if r.ok:
                winners += 1
                win_ms.append(ms)
            else:
                lose_ms.append(ms)
                error_codes[r.error] += 1
        winners_hist[winners] += 1

        expected_tail = pos + (size if isinstance(base, S3ExpressLog) else 1)
        new_pos = base.tail()
        if winners != 1 or new_pos != expected_tail:
            integrity_violations.append({"round": rnd, "at": pos, "winners": winners, "tail": new_pos})
        pos = new_pos

    out = {
        "writers": writers,
        "rounds": rounds,
        "winners_per_round": {str(k): v for k, v in sorted(winners_hist.items())},
        "loser_error_codes": dict(error_codes),
        "winner_latency_ms": summarize(win_ms),
        "loser_latency_ms": summarize(lose_ms),
        "integrity_violations": integrity_violations[:20],
        "integrity_violation_count": len(integrity_violations),
    }
    verdict = "OK" if not integrity_violations else f"{len(integrity_violations)} VIOLATION(S)"
    print(f"  {writers} writers x {rounds} rounds: {verdict}; winners/round {out['winners_per_round']}")
    print(f"  loser errors {dict(error_codes)}")
    print(f"  winner {fmt(out['winner_latency_ms'])}")
    print(f"  loser  {fmt(out['loser_latency_ms'])}")
    return out


def fmt(s: dict) -> str:
    if not s.get("count"):
        return "n=0"
    return f"n={s['count']} p50={s['p50']} p90={s['p90']} p99={s['p99']} p999={s['p999']} max={s['max']} ms"


def ec2_placement() -> dict | None:
    """AZ of the client if running on EC2 (IMDSv2); co-location dominates S3 Express latency."""
    import urllib.request

    try:
        req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        token = urllib.request.urlopen(req, timeout=0.3).read().decode()
        get = lambda p: urllib.request.urlopen(  # noqa: E731
            urllib.request.Request(f"http://169.254.169.254/latest/meta-data/{p}", headers={"X-aws-ec2-metadata-token": token}),
            timeout=0.3,
        ).read().decode()
        return {"az": get("placement/availability-zone"), "az_id": get("placement/availability-zone-id"), "instance_type": get("instance-type")}
    except Exception:  # noqa: BLE001 - not on EC2
        return None


# --- CLI ------------------------------------------------------------------------


def int_list(s: str) -> list[int]:
    return [int(x) for x in s.split(",") if x]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("backend", choices=["s3x", "s2", "mem"])
    p.add_argument("--tests", default="latency,throughput,race")
    p.add_argument("--bucket", help="s3x: directory bucket, e.g. mybench--use1-az4--x-s3")
    p.add_argument("--region", help="s3x: region of the directory bucket, e.g. us-east-1")
    p.add_argument("--prefix", default="logbench", help="s3x: key prefix")
    p.add_argument("--basin", help="s2: basin name (token in S2_API_KEY)")
    p.add_argument("--stream-prefix", default="logbench", help="s2: stream name prefix")
    p.add_argument("--mem-latency-ms", type=float, default=1.0)
    p.add_argument("--sizes", type=int_list, default=[256, 4 * KiB, 64 * KiB, 512 * KiB])
    p.add_argument("--n", type=int, default=1000, help="latency samples per size")
    p.add_argument("--warmup", type=int, default=20)
    p.add_argument("--tp-size", type=int, default=64 * KiB)
    p.add_argument("--seconds", type=float, default=60)
    p.add_argument("--parallel", type=int_list, default=[1, 4, 16])
    p.add_argument("--race-writers", type=int, default=8)
    p.add_argument("--race-rounds", type=int, default=200)
    p.add_argument("--race-size", type=int, default=1 * KiB)
    p.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = p.parse_args()

    if args.backend == "s3x" and not (args.bucket and args.region):
        p.error("s3x needs --bucket and --region")
    if args.backend == "s2" and not (args.basin and os.environ.get("S2_API_KEY")):
        p.error("s2 needs --basin and S2_API_KEY")

    run_id = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    make_log = log_factory(args, run_id)
    tests = args.tests.split(",")
    report = {
        "run_id": run_id,
        "backend": args.backend,
        "args": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "client": {"host": socket.gethostname(), "platform": platform.platform(), "ec2": ec2_placement()},
        "started": time.time(),
    }
    print(f"run {run_id} backend={args.backend} client={report['client']['ec2'] or 'not EC2'}")

    if "latency" in tests:
        print("latency (sequential conditional appends):")
        report["latency"] = run_latency(make_log, args.sizes, args.n, args.warmup)
    if "throughput" in tests:
        print(f"throughput ({args.seconds}s per setting):")
        report["throughput"] = [run_throughput(make_log, args.tp_size, args.seconds, k) for k in args.parallel]
    if "race" in tests:
        print("race (concurrent appends at the same position):")
        report["race"] = run_race(make_log, args.race_writers, args.race_rounds, args.race_size)

    report["finished"] = time.time()
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"{args.backend}-{run_id}.json"
    path.write_text(json.dumps(report, indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
