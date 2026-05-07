_STEMS_KR   = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
_BRANCHES_KR = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

STEM_TO_KR = {
    "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
    "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계",
}
BRANCH_TO_KR = {
    "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
    "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해",
}


def year_ganji(year: int) -> str:
    offset = (year - 1984) % 60
    return _STEMS_KR[offset % 10] + _BRANCHES_KR[offset % 12]


def stem_to_korean(stem: str) -> str:
    return STEM_TO_KR.get(stem, stem)


def branch_to_korean(branch: str) -> str:
    return BRANCH_TO_KR.get(branch, branch)
