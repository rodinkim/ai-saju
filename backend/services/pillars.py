from schemas.saju import FourPillars, GwiinItem, Pillar, SinsalItem
from services.ganji import EARTHLY_BRANCHES, EARTHLY_BRANCHES_KR, HEAVENLY_STEMS, HEAVENLY_STEMS_KR
from services.sinsal import calculate_gwiin_sinsal

# 절기(節氣) 기준일 (월, 일) — 평균 근사값 ±1~2일
JEOLGI_DATES  = [(1,6),(2,4),(3,6),(4,5),(5,6),(6,6),(7,7),(8,7),(9,8),(10,8),(11,7),(12,7)]
# 절기 순서에 대응하는 지지 인덱스: 소한=丑(1), 입춘=寅(2), ..., 대설=子(0)
JEOLGI_BRANCH = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]


def get_year_pillar(year: int) -> Pillar:
    """년주 계산. 기준: 1984년 = 甲子(갑자), 60갑자 반복"""
    offset = (year - 1984) % 60
    stem_idx   = offset % 10
    branch_idx = offset % 12
    return Pillar(
        heavenly_stem=HEAVENLY_STEMS[stem_idx],
        earthly_branch=EARTHLY_BRANCHES[branch_idx],
        korean=HEAVENLY_STEMS_KR[stem_idx] + EARTHLY_BRANCHES_KR[branch_idx],
    )


def _get_saju_month(month: int, day: int) -> tuple[int, int]:
    """절기 기준 (지지 인덱스, 사주 월 번호 1=寅~12=丑) 반환"""
    jeolgi_day = JEOLGI_DATES[month - 1][1]
    if day >= jeolgi_day:
        branch_idx = JEOLGI_BRANCH[month - 1]
    else:
        prev = month - 2 if month > 1 else 11
        branch_idx = JEOLGI_BRANCH[prev]
    saju_month_num = (branch_idx - 2 + 12) % 12 + 1
    return branch_idx, saju_month_num


def get_month_pillar(year: int, month: int, day: int) -> Pillar:
    """월주 계산. 절기 기준 + 오호둔월법(五虎遁月法)으로 천간 산출."""
    year_stem_idx = (year - 1984) % 10
    branch_idx, saju_month_num = _get_saju_month(month, day)

    # 오호둔월법: 甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅
    month_stem_base = [2, 4, 6, 8, 0]
    stem_start = month_stem_base[year_stem_idx % 5]
    stem_idx = (stem_start + saju_month_num - 1) % 10

    return Pillar(
        heavenly_stem=HEAVENLY_STEMS[stem_idx],
        earthly_branch=EARTHLY_BRANCHES[branch_idx],
        korean=HEAVENLY_STEMS_KR[stem_idx] + EARTHLY_BRANCHES_KR[branch_idx],
    )


def get_day_pillar(year: int, month: int, day: int) -> Pillar:
    """일주 계산. Julian Day Number 기반 60갑자 순환."""
    if month < 3:
        month += 12
        year -= 1
    a = year // 100
    b = 2 - a + a // 4
    jdn = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524

    offset = jdn - 2415021  # 기준: 1900-01-01 = 甲戌
    stem_idx   = (10 + offset) % 10
    branch_idx = (10 + offset) % 12

    return Pillar(
        heavenly_stem=HEAVENLY_STEMS[stem_idx],
        earthly_branch=EARTHLY_BRANCHES[branch_idx],
        korean=HEAVENLY_STEMS_KR[stem_idx] + EARTHLY_BRANCHES_KR[branch_idx],
    )


def get_hour_pillar(day_stem_idx: int, hour: int, minute: int = 0) -> Pillar:
    """시주 계산. 오자둔시법(五子遁時法) 적용."""
    total_min    = hour * 60 + minute
    adjusted_hour = ((total_min - 30) % 1440) // 60
    branch_idx   = ((adjusted_hour + 1) // 2) % 12

    # 오자둔시법: 甲己→甲子, 乙庚→丙子, 丙辛→戊子, 丁壬→庚子, 戊癸→壬子
    hour_stem_base = [0, 2, 4, 6, 8]
    stem_start = hour_stem_base[day_stem_idx % 5]
    stem_idx   = (stem_start + branch_idx) % 10

    return Pillar(
        heavenly_stem=HEAVENLY_STEMS[stem_idx],
        earthly_branch=EARTHLY_BRANCHES[branch_idx],
        korean=HEAVENLY_STEMS_KR[stem_idx] + EARTHLY_BRANCHES_KR[branch_idx],
    )


def calculate_four_pillars(year: int, month: int, day: int, hour: int, minute: int) -> FourPillars:
    year_pillar  = get_year_pillar(year)
    month_pillar = get_month_pillar(year, month, day)
    day_pillar   = get_day_pillar(year, month, day)

    day_stem_idx = HEAVENLY_STEMS.index(day_pillar.heavenly_stem)
    hour_pillar  = get_hour_pillar(day_stem_idx, hour, minute)

    fp_base = FourPillars(
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar,
    )
    gwiin, gwiin_details_raw, sinsal_raw = calculate_gwiin_sinsal(fp_base)

    return FourPillars(
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar,
        gwiin=gwiin,
        gwiin_details=[
            GwiinItem(
                name=g["name"],
                basis=g["basis"],
                matched=g.get("matched", []),
                weakened=g.get("weakened", False),
                weaken_reason=g.get("weaken_reason", ""),
            ) for g in gwiin_details_raw
        ],
        sinsal=[SinsalItem(name=s["name"], pillar=s["pillar"], basis=s["basis"]) for s in sinsal_raw],
    )
