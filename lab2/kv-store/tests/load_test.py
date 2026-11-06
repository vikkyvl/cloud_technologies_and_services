import argparse
import asyncio
import csv
import os
import random
import statistics
import time
import uuid

import httpx

TABLE = "bench"
CSV_FIELDS = ["label", "phase", "operations", "errors", "seconds", "throughput",
              "avg_ms", "p50_ms", "p95_ms", "p99_ms", "max_ms"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load test of the key-value store")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--label", required=True)
    parser.add_argument("--records", type=int, default=1000)
    parser.add_argument("--operations", type=int, default=5000)
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--read-ratio", type=float, default=0.5)
    parser.add_argument("--write-quorum", type=int)
    parser.add_argument("--read-quorum", type=int)
    parser.add_argument("--output", default="load_results.csv")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def summarize(label: str, phase: str, latencies: list[float], errors: int,
              seconds: float) -> dict:
    ordered = sorted(latencies)
    centiles = statistics.quantiles(ordered, n=100) if len(ordered) > 1 else ordered * 99

    return {
        "label": label,
        "phase": phase,
        "operations": len(latencies),
        "errors": errors,
        "seconds": round(seconds, 2),
        "throughput": round(len(latencies) / seconds, 1),
        "avg_ms": round(statistics.mean(ordered), 2),
        "p50_ms": round(centiles[49], 2),
        "p95_ms": round(centiles[94], 2),
        "p99_ms": round(centiles[98], 2),
        "max_ms": round(ordered[-1], 2),
    }


async def timed(client: httpx.AsyncClient, method: str, path: str,
                body: dict | None = None) -> tuple[float, bool]:
    started = time.perf_counter()
    try:
        response = await client.request(method, path, json=body)
        ok = response.status_code < 400
    except httpx.HTTPError:
        ok = False

    return (time.perf_counter() - started) * 1000, ok


async def run_phase(client: httpx.AsyncClient, requests: list[tuple[str, str, dict | None]],
                    concurrency: int) -> tuple[list[float], int, float]:
    queue: asyncio.Queue = asyncio.Queue()
    for request in requests:
        queue.put_nowait(request)

    latencies: list[float] = []
    errors = 0

    async def worker() -> None:
        nonlocal errors
        while not queue.empty():
            method, path, body = queue.get_nowait()
            latency, ok = await timed(client, method, path, body)
            latencies.append(latency)
            errors += 0 if ok else 1

    started = time.perf_counter()
    await asyncio.gather(*(worker() for _ in range(concurrency)))

    return latencies, errors, time.perf_counter() - started


async def prepare(client: httpx.AsyncClient, args: argparse.Namespace) -> None:
    response = await client.post("/tables", json={"name": TABLE, "partition_key": "id"})
    if response.status_code not in (201, 409):
        response.raise_for_status()

    if args.write_quorum is not None and args.read_quorum is not None:
        quorum = {"write_quorum": args.write_quorum, "read_quorum": args.read_quorum}
        response = await client.put("/internal/quorum", json=quorum)
        response.raise_for_status()
        print("Quorum:", response.json())


def save(rows: list[dict], path: str) -> None:
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def show(rows: list[dict]) -> None:
    print(f"\n{'phase':<8}{'ops':>7}{'err':>6}{'ops/s':>9}{'avg':>8}{'p50':>8}"
          f"{'p95':>8}{'p99':>8}{'max':>9}")
    for row in rows:
        print(f"{row['phase']:<8}{row['operations']:>7}{row['errors']:>6}{row['throughput']:>9}"
              f"{row['avg_ms']:>8}{row['p50_ms']:>8}{row['p95_ms']:>8}{row['p99_ms']:>8}"
              f"{row['max_ms']:>9}")


async def main() -> None:
    args = parse_args()
    random_generator = random.Random(args.seed)
    run_id = uuid.uuid4().hex[:6]
    keys = [f"{run_id}-{index}" for index in range(args.records)]
    item_path = f"/tables/{TABLE}/items/{{key}}"

    limits = httpx.Limits(max_connections=args.concurrency)
    async with httpx.AsyncClient(base_url=args.url, timeout=10, limits=limits) as client:
        await prepare(client, args)

        inserts = [("PUT", item_path.format(key=key), {"n": index, "payload": "x" * 100})
                   for index, key in enumerate(keys)]

        mixed = []
        for index in range(args.operations):
            key = random_generator.choice(keys)
            if random_generator.random() < args.read_ratio:
                mixed.append(("GET", item_path.format(key=key), None))
            else:
                mixed.append(("PATCH", item_path.format(key=key), {"n": index, "payload": "y" * 100}))

        rows = []
        for phase, requests in (("load", inserts), ("run", mixed)):
            latencies, errors, seconds = await run_phase(client, requests, args.concurrency)
            rows.append(summarize(args.label, phase, latencies, errors, seconds))

    print(f"\nLabel {args.label}, records {args.records}, operations {args.operations}, "
          f"concurrency {args.concurrency}, read ratio {args.read_ratio}")
    show(rows)
    save(rows, args.output)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
