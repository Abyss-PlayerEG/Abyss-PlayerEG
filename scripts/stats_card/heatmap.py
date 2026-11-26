#!/usr/bin/env python3
"""Weekday × hour commit-time matrix for the heatmap band."""

from datetime import datetime

TZ_OFFSET = 8  # UTC+8 (Asia/Shanghai)
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def build_matrix(times, tz_offset: int = TZ_OFFSET) -> list[list[int]]:
    """Bucket ISO commit timestamps into a 7×24 (weekday × local hour) matrix."""
    matrix = [[0] * 24 for _ in range(7)]
    for iso in times:
        try:
            dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        except ValueError:
            continue
        shifted = dt.hour + tz_offset
        day = (dt.weekday() + (1 if shifted >= 24 else 0)) % 7
        matrix[day][shifted % 24] += 1
    return matrix


def classify(matrix) -> list[list[int]]:
    """Quantile-based levels 0-4 (0 = empty cell)."""
    vals = sorted(v for row in matrix for v in row if v > 0)
    if not vals:
        return [[0] * 24 for _ in range(7)]

    def q(p: float) -> int:
        return vals[min(len(vals) - 1, int(len(vals) * p))]

    t1 = max(1, q(0.25))
    t2 = max(t1 + 1, q(0.50))
    t3 = max(t2 + 1, q(0.75))
    return [
        [
            0 if v == 0 else 1 if v <= t1 else 2 if v <= t2 else 3 if v <= t3 else 4
            for v in row
        ]
        for row in matrix
    ]
