#!/usr/bin/env python3
"""Bootstrap Wave 5 UT / remaining packs (CH, AN, LD, LA, JK, SK, PY)."""
from __future__ import annotations

import importlib.util

spec = importlib.util.spec_from_file_location(
    "wave4",
    __file__.replace("bootstrap_wave5_state_packs.py", "bootstrap_wave4_state_packs.py"),
)
wave4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wave4)  # type: ignore

WAVE5: dict[str, dict] = {
    "ch": {
        "hc": "hc_punjab_haryana",
        "districts": ["chandigarh"],
        "cdrc": ["chandigarh", "sector_34", "manimajra", "daria"],
    },
    "an": {
        "hc": "hc_calcutta_bench_port_blair",
        "districts": ["port_blair", "south_andaman"],
        "cdrc": ["port_blair", "haddo", "garacharma", "ferrargunj"],
    },
    "ld": {
        "hc": "hc_kerala",
        "districts": ["kavaratti"],
        "cdrc": ["kavaratti", "agatti", "minicoy", "andrott"],
    },
    "la": {
        "hc": "hc_jammu_kashmir_ladakh",
        "districts": ["leh", "kargil"],
        "cdrc": ["leh", "kargil", "nubra", "zanskar"],
    },
    "jk": {
        "hc": "hc_jammu_kashmir_ladakh",
        "districts": ["srinagar", "jammu", "anantnag", "baramulla", "udhampur"],
        "cdrc": ["srinagar", "jammu", "anantnag", "baramulla"],
    },
    "sk": {
        "hc": "hc_sikkim",
        "districts": ["gangtok", "namchi", "gyalshing", "mangan"],
        "cdrc": ["gangtok", "namchi", "gyalshing", "mangan"],
    },
    "py": {
        "hc": "hc_madras",
        "districts": ["puducherry", "karaikal", "mahe", "yanam"],
        "cdrc": ["puducherry", "karaikal", "mahe", "yanam"],
    },
}

wave4.WAVE4 = WAVE5
wave4.NAMES.update({
    "ch": "Chandigarh", "an": "Andaman and Nicobar Islands", "ld": "Lakshadweep",
    "la": "Ladakh", "jk": "Jammu and Kashmir", "sk": "Sikkim", "py": "Puducherry",
})


def main() -> None:
    total = 0
    for st in WAVE5:
        e, r = wave4.bootstrap_state(st, WAVE5[st])
        print(f"{st}: +{e} entities, {r} rel edges")
        total += e
    print(f"TOTAL: +{total} entity files")


if __name__ == "__main__":
    main()
