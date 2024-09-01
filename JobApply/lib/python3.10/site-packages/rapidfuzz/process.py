# SPDX-License-Identifier: MIT
# Copyright (C) 2022 Max Bachmann

from __future__ import annotations

from rapidfuzz._utils import fallback_import as _fallback_import

_mod = "rapidfuzz.process"
extract = _fallback_import(_mod, "extract")
extractOne = _fallback_import(_mod, "extractOne")
extract_iter = _fallback_import(_mod, "extract_iter")
cdist = _fallback_import(_mod, "cdist")
cpdist = _fallback_import(_mod, "cpdist")
