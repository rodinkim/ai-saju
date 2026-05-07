HEAVENLY_STEMS    = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
HEAVENLY_STEMS_KR = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]

EARTHLY_BRANCHES    = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
EARTHLY_BRANCHES_KR = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

STEM_TO_KR = dict(zip(HEAVENLY_STEMS, HEAVENLY_STEMS_KR))
BRANCH_TO_KR = dict(zip(EARTHLY_BRANCHES, EARTHLY_BRANCHES_KR))


def year_ganji(year: int) -> str:
    offset = (year - 1984) % 60
    return HEAVENLY_STEMS_KR[offset % 10] + EARTHLY_BRANCHES_KR[offset % 12]


def stem_to_korean(stem: str) -> str:
    return STEM_TO_KR.get(stem, stem)


def branch_to_korean(branch: str) -> str:
    return BRANCH_TO_KR.get(branch, branch)
