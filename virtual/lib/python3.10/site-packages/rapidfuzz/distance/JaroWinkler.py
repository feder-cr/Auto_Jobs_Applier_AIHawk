# SPDX-License-Identifier: MIT
# Copyright (C) 2022 Max Bachmann
from __future__ import annotations

from rapidfuzz._utils import fallback_import as _fallback_import

_mod = "rapidfuzz.distance.metrics"
distance = _fallback_import(_mod, "jaro_winkler_distance")
similarity = _fallback_import(_mod, "jaro_winkler_similarity")
normalized_distance = _fallback_import(_mod, "jaro_winkler_normalized_distance")
normalized_similarity = _fallback_import(_mod, "jaro_winkler_normalized_similarity")
