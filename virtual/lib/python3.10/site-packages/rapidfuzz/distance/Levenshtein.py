# SPDX-License-Identifier: MIT
# Copyright (C) 2022 Max Bachmann
"""
The Levenshtein (edit) distance is a string metric to measure the
difference between two strings/sequences s1 and s2.
It's defined as the minimum number of insertions, deletions or
substitutions required to transform s1 into s2.
"""
from __future__ import annotations

from rapidfuzz._utils import fallback_import as _fallback_import

_mod = "rapidfuzz.distance.metrics"
distance = _fallback_import(_mod, "levenshtein_distance")
similarity = _fallback_import(_mod, "levenshtein_similarity")
normalized_distance = _fallback_import(_mod, "levenshtein_normalized_distance")
normalized_similarity = _fallback_import(_mod, "levenshtein_normalized_similarity")
editops = _fallback_import(_mod, "levenshtein_editops")
opcodes = _fallback_import(_mod, "levenshtein_opcodes")
