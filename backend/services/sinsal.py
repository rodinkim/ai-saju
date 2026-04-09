"""
귀인(貴人) 및 신살(神煞) 계산 모듈
"""
from __future__ import annotations

HEAVENLY_STEMS  = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# ── 귀인 ────────────────────────────────────────────────────────

# 천을귀인: 일간 → 해당 지지 목록
CHEONUL: dict[str, list[str]] = {
    "甲": ["丑","未"], "戊": ["丑","未"], "庚": ["丑","未"],
    "乙": ["子","申"], "己": ["子","申"],
    "丙": ["亥","酉"], "丁": ["亥","酉"],
    "壬": ["卯","巳"], "癸": ["卯","巳"],
    "辛": ["午","寅"],
}

# 문창귀인: 일간 → 지지
MUNCHANG: dict[str, str] = {
    "甲":"巳","乙":"午","丙":"申","丁":"酉",
    "戊":"申","己":"酉","庚":"亥","辛":"子",
    "壬":"寅","癸":"卯",
}

# 학당귀인(장생지): 일간 → 지지
HAKDANG: dict[str, str] = {
    "甲":"亥","乙":"午",
    "丙":"寅","戊":"寅",
    "丁":"酉","己":"酉",
    "庚":"巳","辛":"子",
    "壬":"申","癸":"卯",
}

# 암록귀인: 일간 → 지지
AMROK: dict[str, str] = {
    "甲":"亥","乙":"戌","丙":"申","丁":"未",
    "戊":"申","己":"未","庚":"巳","辛":"辰",
    "壬":"寅","癸":"丑",
}

# 태극귀인: 일간 -> 지지 목록
TAEGEUK: dict[str, list[str]] = {
    "甲": ["子", "午"], "乙": ["子", "午"],
    "丙": ["卯", "酉"], "丁": ["卯", "酉"],
    "戊": ["辰", "戌", "丑", "未"], "己": ["辰", "戌", "丑", "未"],
    "庚": ["寅", "亥"], "辛": ["寅", "亥"],
    "壬": ["巳", "申"], "癸": ["巳", "申"],
}

# 월덕귀인: 월지(삼합 그룹) -> 천간
WOLDEOK: dict[str, str] = {
    "寅": "丙", "午": "丙", "戌": "丙",
    "申": "壬", "子": "壬", "辰": "壬",
    "亥": "甲", "卯": "甲", "未": "甲",
    "巳": "庚", "酉": "庚", "丑": "庚",
}

# 천덕귀인: 월지 -> 천간
CHEONDEOK: dict[str, str] = {
    "寅": "丁", "卯": "申", "辰": "壬",
    "巳": "辛", "午": "亥", "未": "甲",
    "申": "癸", "酉": "寅", "戌": "丙",
    "亥": "乙", "子": "巳", "丑": "庚",
}

# 삼기귀인: 천간 조합
SAMGI_SETS: dict[str, set[str]] = {
    "천상삼기": {"甲", "戊", "庚"},
    "지하삼기": {"乙", "丙", "丁"},
    "인중삼기": {"壬", "癸", "辛"},
}

# 지지 충 관계
CHUNG_PAIR: dict[str, str] = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# ── 신살 ────────────────────────────────────────────────────────

# 삼합 그룹: 지지 → 화/수/금/목
SAMSAM: dict[str, str] = {
    "寅":"화","午":"화","戌":"화",
    "申":"수","子":"수","辰":"수",
    "巳":"금","酉":"금","丑":"금",
    "亥":"목","卯":"목","未":"목",
}

# 12신살 전체: 삼합 그룹 → {신살명: 지지}
# 순서: 겁살→재살→천살→지살→도화살(년살)→월살→망신살→장성살→반안살→역마살→육해살→화개살
SINSAL_POS: dict[str, dict[str, str]] = {
    "화": {
        "겁살":"亥","재살":"子","천살":"丑","지살":"寅",
        "도화살":"卯","월살":"辰","망신살":"巳","장성살":"午",
        "반안살":"未","역마살":"申","육해살":"酉","화개살":"戌",
    },
    "수": {
        "겁살":"巳","재살":"午","천살":"未","지살":"申",
        "도화살":"酉","월살":"戌","망신살":"亥","장성살":"子",
        "반안살":"丑","역마살":"寅","육해살":"卯","화개살":"辰",
    },
    "금": {
        "겁살":"寅","재살":"卯","천살":"辰","지살":"巳",
        "도화살":"午","월살":"未","망신살":"申","장성살":"酉",
        "반안살":"戌","역마살":"亥","육해살":"子","화개살":"丑",
    },
    "목": {
        "겁살":"申","재살":"酉","천살":"戌","지살":"亥",
        "도화살":"子","월살":"丑","망신살":"寅","장성살":"卯",
        "반안살":"辰","역마살":"巳","육해살":"午","화개살":"未",
    },
}

# 양인살: 일간 → 지지
YANGIN: dict[str, str] = {
    "甲":"卯","乙":"寅",
    "丙":"午","戊":"午",
    "丁":"巳","己":"巳",
    "庚":"酉","辛":"申",
    "壬":"子","癸":"亥",
}

# 공망: 일주(천간+지지) → 공망 지지 2개
def _build_gongmang() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for i in range(60):
        stem   = HEAVENLY_STEMS[i % 10]
        branch = EARTHLY_BRANCHES[i % 12]
        start  = (i // 10 * 10) % 12
        used   = {EARTHLY_BRANCHES[(start + k) % 12] for k in range(10)}
        result[stem + branch] = [b for b in EARTHLY_BRANCHES if b not in used]
    return result

GONGMANG: dict[str, list[str]] = _build_gongmang()


# ── 메인 계산 함수 ───────────────────────────────────────────────

def calculate_gwiin_sinsal(fp) -> tuple[list[str], list[dict], list[dict]]:
    """
    FourPillars 객체를 받아 (귀인 이름 목록, 귀인 상세, 신살 목록)을 반환.
    귀인 항목: {"name": str, "basis": str, "matched": list[str], "weakened": bool, "weaken_reason": str}
    신살 항목: {"name": str, "pillar": str, "basis": str}
    (pillar = 년/월/일/시, basis = 년지기준/일지기준/일주기준)
    """
    day_stem = fp.day_pillar.heavenly_stem

    branches = [
        ("년", fp.year_pillar.earthly_branch),
        ("월", fp.month_pillar.earthly_branch),
        ("일", fp.day_pillar.earthly_branch),
        ("시", fp.hour_pillar.earthly_branch),
    ]
    stems = [
        ("년", fp.year_pillar.heavenly_stem),
        ("월", fp.month_pillar.heavenly_stem),
        ("일", fp.day_pillar.heavenly_stem),
        ("시", fp.hour_pillar.heavenly_stem),
    ]
    branch_values = [b for _, b in branches]
    stem_values = [s for _, s in stems]

    # ── 귀인 ──────────────────────────────────────────────────────
    gwiin: list[str] = []
    gwiin_details: list[dict] = []
    gwiin_seen: set[tuple[str, str]] = set()
    day_key = fp.day_pillar.heavenly_stem + fp.day_pillar.earthly_branch
    gongmang_branches = set(GONGMANG.get(day_key, []))

    def _weaken_info(targets: list[str]) -> tuple[bool, str]:
        hit_targets = [t for t in targets if t in branch_values]
        if not hit_targets:
            return False, ""
        if any(CHUNG_PAIR.get(t) in branch_values for t in hit_targets):
            return True, "충"
        if any(t in gongmang_branches for t in hit_targets):
            return True, "공망"
        return False, ""

    def add_gwiin(name: str, basis: str, matched: list[str], target_branches: list[str] | None = None) -> None:
        key = (name, basis)
        if key in gwiin_seen:
            return
        gwiin_seen.add(key)
        weakened, reason = _weaken_info(target_branches or [])
        gwiin_details.append(
            {
                "name": name,
                "basis": basis,
                "matched": matched,
                "weakened": weakened,
                "weaken_reason": reason,
            }
        )
        if name not in gwiin:
            gwiin.append(name)

    # 일간 기준 귀인
    cheonul_targets = CHEONUL.get(day_stem, [])
    cheonul_hit = [f"{label}지:{branch}" for label, branch in branches if branch in cheonul_targets]
    if cheonul_hit:
        add_gwiin("천을귀인", "일간기준", cheonul_hit, cheonul_targets)

    munchang_target = MUNCHANG.get(day_stem)
    munchang_hit = [f"{label}지:{branch}" for label, branch in branches if branch == munchang_target]
    if munchang_hit:
        add_gwiin("문창귀인", "일간기준", munchang_hit, [munchang_target] if munchang_target else [])

    hakdang_target = HAKDANG.get(day_stem)
    hakdang_hit = [f"{label}지:{branch}" for label, branch in branches if branch == hakdang_target]
    if hakdang_hit:
        add_gwiin("학당귀인", "일간기준", hakdang_hit, [hakdang_target] if hakdang_target else [])

    amrok_target = AMROK.get(day_stem)
    amrok_hit = [f"{label}지:{branch}" for label, branch in branches if branch == amrok_target]
    if amrok_hit:
        add_gwiin("암록귀인", "일간기준", amrok_hit, [amrok_target] if amrok_target else [])

    taegeuk_targets = TAEGEUK.get(day_stem, [])
    taegeuk_hit = [f"{label}지:{branch}" for label, branch in branches if branch in taegeuk_targets]
    if taegeuk_hit:
        add_gwiin("태극귀인", "일간기준", taegeuk_hit, taegeuk_targets)

    # 월지 기준 귀인
    month_branch = fp.month_pillar.earthly_branch
    woldeok_target = WOLDEOK.get(month_branch)
    woldeok_hit = [f"{label}간:{stem}" for label, stem in stems if stem == woldeok_target]
    if woldeok_hit:
        add_gwiin("월덕귀인", "월지기준", woldeok_hit)

    cheondeok_target = CHEONDEOK.get(month_branch)
    cheondeok_hit = [f"{label}간:{stem}" for label, stem in stems if stem == cheondeok_target]
    if cheondeok_hit:
        add_gwiin("천덕귀인", "월지기준", cheondeok_hit)

    # 천간 조합 귀인
    stem_set = set(stem_values)
    for label, target_set in SAMGI_SETS.items():
        if target_set.issubset(stem_set):
            add_gwiin("삼기귀인", "천간조합기준", [label])

    # ── 신살 ──────────────────────────────────────────────────────
    sinsal: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(name: str, pillar: str, basis: str) -> None:
        key = (name, pillar, basis)
        if key not in seen:
            seen.add(key)
            sinsal.append({"name": name, "pillar": pillar, "basis": basis})

    # 12신살: 년지 기준 + 일지 기준
    for base_branch, basis in [
        (fp.year_pillar.earthly_branch, "년지기준"),
        (fp.day_pillar.earthly_branch, "일지기준"),
    ]:
        group = SAMSAM.get(base_branch)
        if not group:
            continue
        for name, target in SINSAL_POS[group].items():
            for label, branch in branches:
                if branch == target:
                    add(name, label, basis)

    # 양인살 (일간 기준)
    yangin_target = YANGIN.get(day_stem)
    if yangin_target:
        for label, branch in branches:
            if branch == yangin_target:
                add("양인살", label, "일간기준")

    # 공망 (일주 기준)
    for label, branch in branches:
        if branch in GONGMANG.get(day_key, []):
            add("공망", label, "일주기준")

    return gwiin, gwiin_details, sinsal
