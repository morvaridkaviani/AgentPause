"""Deterministic, order-independent random streams.

Every random draw is derived from a key such as ``(seed, scenario, episode, "mistake", id)``.
The result does not depend on how many other draws came before it. This gives:

* **Common random numbers**: every policy sees the same injected mistakes and wrong
  assumptions for a given seed and episode, so comparisons are paired.
* **Resumability**: an interactive episode can be stored as JSON and resumed in another
  process with identical behaviour, without serializing RNG state.
"""

from __future__ import annotations

import hashlib
import random


def derive_seed(*parts: object) -> int:
    key = "\x1f".join(str(p) for p in parts)
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")


def derive_rng(*parts: object) -> random.Random:
    return random.Random(derive_seed(*parts))
