# SPDX-License-Identifier: MIT
# Copyright (C) 2022 Max Bachmann

from __future__ import annotations

from rapidfuzz._utils import fallback_import as _fallback_import

__all__ = ["default_process"]

default_process = _fallback_import("rapidfuzz.utils", "default_process")
