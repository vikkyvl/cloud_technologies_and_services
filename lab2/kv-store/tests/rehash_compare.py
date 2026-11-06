import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "coordinator"))

from app.schemas import Shard
from app.storage.hashing import ModuloRouter
from app.storage.ring import ConsistentHashRouter

KEYS = [f"user{index}" for index in range(10_000)]
TWO = [Shard(id=f"shard-{index}", replicas=[], complete=True) for index in range(2)]
THREE = [Shard(id=f"shard-{index}", replicas=[], complete=True) for index in range(3)]


def compare(name, router_before, router_after):
    before = {key: router_before.choose(key, TWO).id for key in KEYS}
    after = {key: router_after.choose(key, THREE).id for key in KEYS}

    moved = sum(before[key] != after[key] for key in KEYS)
    between_old = sum(before[key] != after[key] and after[key] != "shard-2" for key in KEYS)
    distribution = Counter(after.values())

    print(f"{name:<26}{moved:>6} ({moved / len(KEYS):5.1%}){between_old:>14}   "
          + "  ".join(f"{shard.id}={distribution[shard.id]}" for shard in THREE))
    return moved


print(f"Keys: {len(KEYS)}, shards: 2 -> 3, ideal share of the new shard: {len(KEYS) // 3}")
print(f"{'Strategy':<26}{'Moved keys':>14}{'Between old':>14}   Distribution on 3 shards")

compare("hash % N", ModuloRouter(), ModuloRouter())
for vnodes in (1, 10, 100, 500):
    compare(f"consistent, {vnodes} vnodes", ConsistentHashRouter(vnodes), ConsistentHashRouter(vnodes))
