#!/usr/bin/env python3
"""
日柱交叉驗證工具（v2）
使用 ephem（獨立天文庫）vs cantian-tymext（主計算引擎）交叉比對
"""
import sys
import ephem

STEMS = '甲乙丙丁戊己庚辛壬癸'
BRANCHES = '子丑寅卯辰巳午未申酉戌亥'
BASE_JD = ephem.julian_date('1900/1/1')  # 庚子
BASE_CYCLE = 36  # 庚子在60甲子中的index


def ephem_day_pillar(y, m, d):
    """用 ephem 計算日柱（與 cantian-tymext 無關的獨立演算法）"""
    j = ephem.julian_date(f'{y}/{m}/{d}')
    diff = round(j - BASE_JD)
    idx = (diff + BASE_CYCLE) % 60
    return STEMS[idx % 10] + BRANCHES[idx % 12]


def verify_shichen(day_stem, cantian_shichen_list):
    """
    比對 cantian 的時柱列表與本地計算結果
    cantian_shichen_list: list of (branch_name, ganzhi_str)
    """
    day_idx = STEMS.index(day_stem)
    all_match = True
    for i, (name, ganzhi) in enumerate(cantian_shichen_list):
        local = STEMS[(day_idx * 2 + i) % 10] + BRANCHES[i]
        match = local == ganzhi
        if not match:
            all_match = False
            print(f"  ❌ {name} → cantian={ganzhi} local={local}")
    return all_match


if __name__ == '__main__':
    if len(sys.argv) >= 4:
        y, m, d = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
        result = ephem_day_pillar(y, m, d)
        print(f"{y:4d}-{m:02d}-{d:02d} ephem={result}")
