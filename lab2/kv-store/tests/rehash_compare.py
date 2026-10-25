"""How many keys move to another shard when a third shard is added:
simple hash % N versus consistent hashing with virtual nodes.

Run from the kv-store folder:  python tests/rehash_compare.py
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "coordinator"))

from app.schemas import Shard  # noqa: E402
from app.storage.hashing import ModuloRouter  # noqa: E402
from app.storage.ring import ConsistentHashRouter  # noqa: E402

KEYS = [f"user{i}" for i in range(10_000)]
TWO = [Shard(id=f"shard-{i}", url=f"http://shard{i}:8000") for i in range(2)]
THREE = [Shard(id=f"shard-{i}", url=f"http://shard{i}:8000") for i in range(3)]


def compare(name, router_before, router_after):
    before = {k: router_before.choose(k, TWO).id for k in KEYS}
    after = {k: router_after.choose(k, THREE).id for k in KEYS}
    moved = sum(before[k] != after[k] for k in KEYS)
    # keys that moved between the OLD shards (not to the new one)
    between_old = sum(before[k] != after[k] and after[k] != "shard-2" for k in KEYS)
    dist = Counter(after.values())
    print(f"{name:<26}{moved:>6} ({moved / len(KEYS):5.1%}){between_old:>14}   "
          + "  ".join(f"{s.id}={dist[s.id]}" for s in THREE))
    return moved


print(f"Keys: {len(KEYS)}, shards: 2 -> 3, ideal share of the new shard: {len(KEYS) // 3}")
print(f"{'Strategy':<26}{'Moved keys':>14}{'Between old':>14}   Distribution on 3 shards")
compare("hash % N", ModuloRouter(), ModuloRouter())
for vnodes in (1, 10, 100, 500):
    compare(f"consistent, {vnodes} vnodes", ConsistentHashRouter(vnodes), ConsistentHashRouter(vnodes))
