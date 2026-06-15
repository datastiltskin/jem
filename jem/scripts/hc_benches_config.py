"""
HC permanent bench definitions and district→bench routing for JEM generators.
License: CC0
"""

from __future__ import annotations

# (bench_id, display_name, parent_hc_id, seat_city)
HC_BENCHES_DEF: list[tuple[str, str, str, str]] = [
    # Madras HC — sole permanent bench at Madurai (est. 2004); no Tiruchirappalli bench
    ("hc_madras_bench_madurai", "Madurai Bench of Madras High Court", "hc_madras", "Madurai"),
    # Bombay HC
    ("hc_bombay_bench_nagpur", "Nagpur Bench of Bombay High Court", "hc_bombay", "Nagpur"),
    ("hc_bombay_bench_aurangabad", "Aurangabad Bench of Bombay High Court", "hc_bombay", "Aurangabad"),
    ("hc_bombay_bench_panaji", "Panaji Bench of Bombay High Court", "hc_bombay", "Panaji"),
    # Allahabad HC
    ("hc_allahabad_bench_lucknow", "Lucknow Bench of Allahabad High Court", "hc_allahabad", "Lucknow"),
    # Calcutta HC
    ("hc_calcutta_bench_port_blair", "Port Blair Bench of Calcutta High Court", "hc_calcutta", "Port Blair"),
    ("hc_calcutta_bench_jalpaiguri", "Jalpaiguri Bench of Calcutta High Court", "hc_calcutta", "Jalpaiguri"),
    # Rajasthan HC (principal seat Jodhpur)
    ("hc_rajasthan_bench_jaipur", "Jaipur Bench of Rajasthan High Court", "hc_rajasthan", "Jaipur"),
    # Karnataka HC
    ("hc_karnataka_bench_dharwad", "Dharwad Bench of Karnataka High Court", "hc_karnataka", "Dharwad"),
    # Gauhati HC (NE benches)
    ("hc_gauhati_bench_kohima", "Kohima Bench of Gauhati High Court", "hc_gauhati", "Kohima"),
    ("hc_gauhati_bench_aizawl", "Aizawl Bench of Gauhati High Court", "hc_gauhati", "Aizawl"),
    ("hc_gauhati_bench_itanagar", "Itanagar Bench of Gauhati High Court", "hc_gauhati", "Itanagar"),
    # Punjab & Haryana HC
    ("hc_punjab_haryana_bench_shimla", "Shimla Bench of Punjab and Haryana High Court", "hc_punjab_haryana", "Shimla"),
]

# TN district slug → bench id (remainder appeal to parent hc_madras at principal seat)
TN_DISTRICT_TO_BENCH: dict[str, str] = {
    "dindigul": "hc_madras_bench_madurai",
    "kanniyakumari": "hc_madras_bench_madurai",
    "madurai": "hc_madras_bench_madurai",
    "ramanathapuram": "hc_madras_bench_madurai",
    "sivaganga": "hc_madras_bench_madurai",
    "tenkasi": "hc_madras_bench_madurai",
    "theni": "hc_madras_bench_madurai",
    "thoothukudi": "hc_madras_bench_madurai",
    "tirunelveli": "hc_madras_bench_madurai",
    "virudhunagar": "hc_madras_bench_madurai",
}

# MH explicit district entity id → bench id
MH_DISTRICT_TO_BENCH: dict[str, str] = {
    "mh_district_court_nagpur": "hc_bombay_bench_nagpur",
    "mh_district_court_amravati": "hc_bombay_bench_nagpur",
    "mh_district_court_aurangabad": "hc_bombay_bench_aurangabad",
    "mh_district_court_nashik": "hc_bombay_bench_aurangabad",
    "mh_district_court_nanded": "hc_bombay_bench_aurangabad",
    "mh_district_court_solapur": "hc_bombay_bench_aurangabad",
}

# KA explicit district entity id → bench id
KA_DISTRICT_TO_BENCH: dict[str, str] = {
    "ka_district_court_dharwad": "hc_karnataka_bench_dharwad",
    "ka_district_court_belagavi": "hc_karnataka_bench_dharwad",
}

# UP second district stub
UP_DISTRICT_TO_BENCH: dict[str, str] = {
    "up_district_court_varanasi": "hc_allahabad_bench_lucknow",
}

# WB second district
WB_DISTRICT_TO_BENCH: dict[str, str] = {
    "wb_district_court_asansol": "hc_calcutta_bench_jalpaiguri",
}

# RJ second district
RJ_DISTRICT_TO_BENCH: dict[str, str] = {
    "rj_district_court_jaipur": "hc_rajasthan_bench_jaipur",
}

PARENT_HC_BY_BENCH: dict[str, str] = {bid: parent for bid, _, parent, _ in HC_BENCHES_DEF}
