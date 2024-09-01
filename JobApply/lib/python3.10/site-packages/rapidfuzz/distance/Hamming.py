# SPDX-License-Identifier: MIT
# Copyright (C) 2022 Max Bachmann
from __future__ import annotations

from rapidfuzz._utils import fallback_import as _fallback_import

_mod = "rapidfuzz.distance.metrics"
distance = _fallback_import(_mod, "hamming_distance")
similarity = _fallback_import(_mod, "hamming_similarity")
normalized_similarity = _fallback_import(_mod, "hamming_normalized_similarity")
normalized_distance = _fallback_import(_mod, "hamming_normalized_distance")
editops = _fallback_import(_mod, "hamming_editops")
opcodes = _fallback_import(_mod, "hamming_opcodes")
