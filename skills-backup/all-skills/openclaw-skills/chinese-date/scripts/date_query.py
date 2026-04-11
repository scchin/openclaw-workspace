#!/usr/bin/env python3
"""
Chinese Date Query v3 (2026-03-31)
精確農曆：使用 cantian-tymext (getChineseCalendar) 取得：
  - 二十四節氣（精確，非±1天近似）
  - 黃曆宜忌、二十八宿、彭祖百忌
  - 喜神/貴神/福神/財神方位、沖煞
  - 八字四柱（含藏干、納音、星運、神煞、刑沖合會）
  - 全日12時辰吉凶
"""

import subprocess
import json
import datetime
import sys
import os

# ─── Node modules path finder ──────────────────────────────
NODE_MODULES_DIR = None

def find_node_modules():
    global NODE_MODULES_DIR
    if NODE_MODULES_DIR:
        return NODE_MODULES_DIR
    candidates = [
        '/opt/homebrew/lib/node_modules',  # macOS ARM (Homebrew)
        '/usr/local/lib/node_modules',
        '/usr/lib/node_modules',
    ]
    for candidate in candidates:
        if os.path.isdir(os.path.join(candidate, 'cantian-tymext')):
            NODE_MODULES_DIR = candidate
            return candidate
    return None

# ─── 天干 / 地支 ────────────────────────────────────────
STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 十二時辰名稱（時段）
SHICHEN_HOURS = [
    (23, 1,  '子時'),  # 23:00-01:59
    (1,  3,  '丑時'),
    (3,  5,  '寅時'),
    (5,  7,  '卯時'),
    (7,  9,  '辰時'),
    (9,  11, '巳時'),
    (11, 13, '午時'),
    (13, 15, '未時'),
    (15, 17, '申時'),
    (17, 19, '酉時'),
    (19, 21, '戌時'),
    (21, 23, '亥時'),
]

# 十神對照表（日干視為自己）
STEM_NAMES = {
    # 比肩、比劫
    (0, '甲'): '比肩',  (1, '甲'): '劫財',  (2, '甲'): '食神',  (3, '甲'): '傷官',  (4, '甲'): '偏財',
    (5, '甲'): '正財',  (6, '甲'): '偏印',  (7, '甲'): '正印',  (8, '甲'): '偏官',  (9, '甲'): '正官',
}
STEM_NAMES_DEFAULT = ['比肩', '劫財', '食神', '傷官', '偏財', '正財', '偏印', '正印', '偏官', '正官']

def get_stem_name(stem_idx, day_stem):
    """時干十神（以日干為基準）"""
    offset = (stem_idx - STEMS.index(day_stem)) % 10
    return STEM_NAMES_DEFAULT[offset]

def get_shichen_ganzhi(day_stem, hour):
    """計算指定時辰的干支"""
    day_stem_idx = STEMS.index(day_stem)
    # 時支 index：23-01→0(子), 01-03→1(丑), ...
    # 時辰的起始小時 → branch index
    if 23 <= hour or hour < 1:
        branch_idx = 0
    else:
        branch_idx = (hour + 1) // 2  # 01-03→1, 03-05→2, ...
    stem_idx = (day_stem_idx * 2 + branch_idx) % 10
    return STEMS[stem_idx] + BRANCHES[branch_idx]

def shichen_range(start_h, end_h):
    """格式化時辰時段"""
    if end_h == 0: end_h = 24
    return f"{start_h:02d}:00-{end_h:02d}:00"

# ─── cantian-tymext 整合 ────────────────────────────────
def call_cantian(year, month, day, hour=12, minute=0):
    nm = find_node_modules()
    if not nm:
        return None, None

    solar = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"

    # 同時取 getChineseCalendar（節氣/宜忌/方位）與 buildBaziFromSolar（八字）
    script = f"""
const {{ createRequire }} = require('module');
const req = createRequire('{nm}/');
const {{ getChineseCalendar, buildBaziFromSolar }} = req('cantian-tymext');

const cal = getChineseCalendar({{ year: {year}, month: {month}, day: {day} }});
const bazi = buildBaziFromSolar({{ solarTime: '{solar}' }});

console.log(JSON.stringify({{ cal, bazi }}, null, 2));
"""
    try:
        result = subprocess.run(
            ['node', '-e', script],
            capture_output=True, text=True,
            cwd=nm, timeout=20
        )
        if result.returncode != 0:
            return None, None
        data = json.loads(result.stdout.strip())
        return data.get('cal'), data.get('bazi')
    except Exception:
        return None, None

# ─── 輸出格式化 ─────────────────────────────────────────
def format_yiji(raw_yi, raw_ji):
    """將逗號分隔的宜忌字串格式化為列表"""
    def fmt(s):
        items = [x.strip() for x in s.split(',') if x.strip()]
        return '、'.join(items) if items else '無'
    return fmt(raw_yi), fmt(raw_ji)

def format_weekday_cn(weekday_idx):
    return ['一','二','三','四','五','六','日'][weekday_idx]

def main():
    now = datetime.datetime.now()
    if len(sys.argv) >= 4:
        year   = int(sys.argv[1])
        month  = int(sys.argv[2])
        day    = int(sys.argv[3])
        hour   = int(sys.argv[4]) if len(sys.argv) >= 5 else now.hour
        minute = int(sys.argv[5]) if len(sys.argv) >= 6 else now.minute
    else:
        year   = now.year
        month  = now.month
        day    = now.day
        hour   = now.hour
        minute = now.minute

    date_obj = datetime.date(year, month, day)
    weekday_cn = format_weekday_cn(date_obj.weekday())

    cal, bazi = call_cantian(year, month, day, hour, minute)

    if not cal or not bazi:
        print("錯誤：無法取得干支資訊，請確認 cantian-tymext 已正確安裝")
        print(f"  npm install -g cantian-tymext")
        print(f"  路徑：{find_node_modules()}")
        return

    # ── 基本資訊 ──
    # solar_str 本身已含星期，直接取用
    solar_str = cal.get('公历', f'{year}年{month}月{day}日').replace(f' 星期{weekday_cn}', '')
    lunar_str = cal.get('农历', '')
    zodiac_str = cal.get('生肖', '')
    nayin_str = cal.get('纳音', '無')

    # ── 四柱八字 ──
    year_pillar  = bazi.get('八字', '').split(' ')[0] if bazi.get('八字') else ''
    month_pillar = bazi.get('八字', '').split(' ')[1] if bazi.get('八字') else ''
    day_pillar   = bazi.get('八字', '').split(' ')[2] if bazi.get('八字') else ''
    hour_pillar  = bazi.get('八字', '').split(' ')[3] if bazi.get('八字') else ''
    day_stem     = bazi.get('日柱', {}).get('天干', {}).get('天干', day_pillar[0]) if isinstance(bazi.get('日柱'), dict) else (day_pillar[0] if day_pillar else '')

    # ── 節氣（精確） ──
    st = cal.get('节气', {})
    term_str = st.get('term', '')
    after_str = f"已過{st.get('afterDays', 0)}日" if st.get('afterDays') else ''
    next_term_str = st.get('nextTerm', '')
    before_next_str = f"距下一次{st.get('beforeNextTermDays', 0)}日" if st.get('beforeNextTermDays') else ''

    if term_str:
        term_display = f"{term_str}（{after_str}）下次：{next_term_str}（{before_next_str}）"
    else:
        term_display = "（無特殊節氣）"

    # ── 黃曆宜忌 ──
    raw_yi = cal.get('宜', '')
    raw_ji = cal.get('忌', '')
    yi_display, ji_display = format_yiji(raw_yi, raw_ji)

    # ── 二十八宿、彭祖百忌 ──
    xiu_str    = cal.get('二十八宿', '無')
    pengzu_str = cal.get('彭祖百忌', '無')

    # ── 方位 ──
    axes = [
        ('🧧 喜神',    cal.get('喜神方位', '')),
        ('🌟 陽貴神',  cal.get('陽貴神方位', '')),
        ('🌙 陰貴神',  cal.get('陰貴神方位', '')),
        ('🍀 福神',    cal.get('福神方位', '')),
        ('💰 財神',    cal.get('財神方位', '')),
    ]
    dir_display = '  '.join([f"{label} {dir}" for label, dir in axes if dir])

    # ── 沖煞 ──
    chongsha_str = cal.get('冲煞', '無')

    # ── 12時辰（傳統四吉時/四凶時，據清代《協紀辨方書》） ──
    # 四吉時：子丑卯辰巳午未酉戌
    # 四凶時：寅申亥（傳統農民曆認為這三個時辰行事不利）
    SHICHEN_AUSPICIOUS = {'子','丑','卯','辰','巳','午','未','酉','戌'}
    SHICHEN_INAUSPICIOUS = {'寅','申','亥'}

    shichen_lines = []
    for start_h, end_h, name in SHICHEN_HOURS:
        ganzhi = get_shichen_ganzhi(day_stem, start_h)
        stem_char = ganzhi[0]
        branch_char = ganzhi[1]
        stem_idx = STEMS.index(stem_char)
        shichen_name = get_stem_name(stem_idx, day_stem)
        rng = shichen_range(start_h, end_h)

        # 凶時專門標記，吉時依陰陽細分
        if branch_char in SHICHEN_INAUSPICIOUS:
            good_sign = '⚠️  凶'
        elif branch_char in SHICHEN_AUSPICIOUS:
            stem_yy = STEMS.index(stem_char) % 2
            day_yy = STEMS.index(day_stem) % 2
            if stem_yy == day_yy:
                good_sign = '✅ 大吉'
            else:
                good_sign = '✅ 吉'
        else:
            good_sign = '⚠️  凶'

        shichen_lines.append(f"    {name}（{rng}）{ganzhi}  {shichen_name}  {good_sign}")

    # ── 公曆節日 ──
    holiday_str = ''
    if cal.get('公历节日'):
        holiday_str = f"🎖️  {cal.get('公历节日')}"

    # ── 輸出 ──
    width = 54
    sep = "=" * width

    print(sep)
    print(f"  📅 西元：{solar_str}  星期{weekday_cn}")
    if holiday_str:
        print(f"  {holiday_str}")
    print(f"  🌿 節氣：{term_display}")
    print(f"  📆 農曆：{lunar_str}")
    print(f"  🎯 四柱：{year_pillar}年 / {month_pillar}月 / {day_pillar}日 / {hour_pillar}時")
    print(f"  🐾 生肖：{zodiac_str}  納音：{nayin_str}")
    print(f"  🌟 日主：{bazi.get('日主','無')}")
    print(f"  🏠 命宮：{bazi.get('命宫','無')}  身宮：{bazi.get('身宫','無')}")
    print(f"  🔮 胎元：{bazi.get('胎元','無')}  胎息：{bazi.get('胎息','無')}")
    print(f"  ⚡ 沖煞：{chongsha_str}")
    print(f"  📋 二十八宿：{xiu_str}  |  彭祖百忌：{pengzu_str}")
    print(f"  {dir_display}")
    print(f"  ✅ 宜：{yi_display}")
    print(f"  ❌ 忌：{ji_display}")
    print(sep)
    print("  【12時辰】")
    for line in shichen_lines:
        print(line)
    print(sep)

if __name__ == "__main__":
    main()
