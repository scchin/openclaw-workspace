#!/usr/bin/env python3
"""
Chinese Date Query: Solar -> Four Pillars (GanZhi) + Solar Terms + Lunar + HuangLi YiJi
Engine: cantian-tymext (Node.js) for precise GanZhi, Python for date handling
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
    try:
        result = subprocess.run(
            ['npm', 'root', '-g'], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            if os.path.isdir(os.path.join(path, 'cantian-tymext')):
                NODE_MODULES_DIR = path
                return path
    except Exception:
        pass
    candidates = [
        '/opt/homebrew/lib/node_modules',
        '/usr/local/lib/node_modules',
        '/usr/lib/node_modules',
    ]
    for candidate in candidates:
        if os.path.isdir(os.path.join(candidate, 'cantian-tymext')):
            NODE_MODULES_DIR = candidate
            return candidate
    return None

# ─── Lunar date formatter ──────────────────────────────────
LUNAR_MONTHS = ['', '正月','二月','三月','四月','五月','六月',
                 '七月','八月','九月','十月','冬月','臘月']

LUNAR_DAYS = ['', '初一','初二','初三','初四','初五','初六','初七',
              '初八','初九','初十','十一','十二','十三','十四','十五',
              '十六','十七','十八','十九','二十','廿一','廿二','廿三',
              '廿四','廿五','廿六','廿七','廿八','廿九','三十']

def format_lunar(year, month, day):
    """Get natural lunar date string using lunarcalendar."""
    try:
        from lunarcalendar import Converter
        d = datetime.date(year, month, day)
        lunar = Converter.Solar2Lunar(d)
        prefix = '閏' if lunar.isleap else ''
        day_str = LUNAR_DAYS[lunar.day] if lunar.day <= 30 else str(lunar.day)
        return f"{lunar.year}年{prefix}{LUNAR_MONTHS[lunar.month]}{day_str}"
    except Exception:
        return f"{year}年{month}月{day}日"

# ─── Get precise GanZhi from cantian-tymext ──────────────
def get_bazi(year, month, day, hour=12, minute=0):
    nm = find_node_modules()
    if not nm:
        return None
    solar = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"
    script = f"""
const {{ createRequire }} = require('module');
const req = createRequire('{nm}/');
const {{ buildBaziFromSolar }} = req('cantian-tymext');
const bazi = buildBaziFromSolar({{ solarTime: '{solar}' }});
const parts = bazi.八字.split(' ');
console.log(JSON.stringify({{
  year: parts[0],
  month: parts[1],
  day: parts[2],
  hour: parts[3],
  zodiac: bazi.生肖,
}}));
"""
    try:
        result = subprocess.run(
            ['node', '-e', script],
            capture_output=True, text=True,
            cwd=nm, timeout=15
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout.strip())
        data['lunar'] = format_lunar(year, month, day)
        return data
    except Exception:
        return None

# ─── Solar terms (approximate dates, ±1 day) ─────────────
SOLAR_TERMS = [
    ("小寒",  1,  5), ("大寒",  1, 20),
    ("立春",  2,  4), ("雨水",  2, 19),
    ("驚蟄",  3,  5), ("春分",  3, 20),
    ("清明",  4,  4), ("穀雨",  4, 20),
    ("立夏",  5,  5), ("小滿",  5, 21),
    ("芒種",  6,  5), ("夏至",  6, 21),
    ("小暑",  7,  7), ("大暑",  7, 22),
    ("立秋",  8,  7), ("處暑",  8, 23),
    ("白露",  9,  7), ("秋分",  9, 23),
    ("寒露", 10,  8), ("霜降", 10, 23),
    ("立冬", 11,  7), ("小雪", 11, 22),
    ("大雪", 12,  7), ("冬至", 12, 21),
]

def get_solar_term(year, month, day):
    d = datetime.date(year, month, day)
    found = []
    for name, m, d_std in SOLAR_TERMS:
        try:
            t = datetime.date(year, m, d_std)
            if abs((d - t).days) <= 1:
                found.append(name)
        except ValueError:
            pass
    return found

# ─── HuangLi YiJi ─────────────────────────────────────────
TERM_EFFECTS = {
    "立春":  ({"納采","訂盟","嫁娶","開市","祭祀","祈福","出行"}, {"搬家","遠行","破土","豎柱"}),
    "雨水":  ({"祭祀","祈雨","播種","補眠","求醫"}, {"動土","破土","搬家","安葬"}),
    "驚蟄":  ({"祭祀","驅蟲","整理","掃舍","出行","沐浴"}, {"破土","動土","嫁娶","安葬"}),
    "春分":  ({"祭祀","祈福","嫁娶","掃墓","豎柱","出行"}, {"動土","破土","吵架","遠行"}),
    "清明":  ({"祭祀","掃墓","踏青","賞花","修造","祈福"}, {"動怒","動土","蓋屋","遠行"}),
    "穀雨":  ({"祭祀","祈雨","播種","納畜","求財","祈福"}, {"大動工程","安葬","破土"}),
    "立夏":  ({"祭祀","出火","納畜","牧養","移徙","求醫"}, {"遠行","搬遷","動土"}),
    "小滿":  ({"祭祀","祈蠶","求神","取魚","祈福"}, {"破土","安葬","動土"}),
    "芒種":  ({"祭祀","祈求","安床","納采","沐浴"}, {"開市","動土","破土"}),
    "夏至":  ({"祭祀","裁衣","納畜","沐浴","祈福"}, {"搬家","動土","破土","遠行"}),
    "小暑":  ({"祭祀","作灶","納財","補運","修行","祈福"}, {"動土","破土","安葬"}),
    "大暑":  ({"祭祀","溫補","減肥","清心","靜心","祈福"}, {"嫁娶","遠行","搬家"}),
    "立秋":  ({"祭祀","祈福","嫁娶","納采","豎柱","出行"}, {"搬家","遠行","搬遷","動土"}),
    "處暑":  ({"祭祀","祈福","捕捉","納畜","沐浴","掃舍"}, {"動土","搬家","破土"}),
    "白露":  ({"祭祀","祈福","納采","嫁娶","出行","沐浴"}, {"破土","動土","安葬"}),
    "秋分":  ({"祭祀","賞月","祈福","團圓","豎柱","出行"}, {"動土","破土","吵架","遠行"}),
    "寒露":  ({"祭祀","登高","賞菊","潤燥","出行","祈福"}, {"搬家","搬遷","動土"}),
    "霜降":  ({"祭祀","掃墓","賞楓","進補","祈福","沐浴"}, {"動土","破土","安葬"}),
    "立冬":  ({"祭祀","補冬","納畜","牧養","移徙","祈福"}, {"搬家","遠行","搬遷","動土"}),
    "小雪":  ({"祭祀","腌製","進補","清心","收拾","祈福"}, {"搬家","搬遷","破土"}),
    "大雪":  ({"祭祀","溫補","進補","靜心","保養","沐浴"}, {"遠行","動土","搬家"}),
    "冬至":  ({"祭祀","祈福","團圓","冬泳","溫補","沐浴"}, {"爭吵","搬家","蓋屋","動土"}),
    "小寒":  ({"祭祀","掃舍","求醫","補眠","靜心","祈福"}, {"嫁娶","動土","破土","安葬"}),
    "大寒":  ({"祭祀","除塵","補水","溫補","打掃","祈福"}, {"搬家","遠行","搬遷","動土"}),
}

def get_yiji(solar_terms):
    yi = set(["祭祀","祈福"])
    ji = set(["動土","破土"])
    for term in solar_terms:
        if term in TERM_EFFECTS:
            yi.update(TERM_EFFECTS[term][0])
            ji.update(TERM_EFFECTS[term][1])
    yi.update({"沐浴","掃舍","整手足甲","求醫","出行"})
    ji.update({"開市","安葬","伐木","嫁娶"})
    ji -= yi
    return sorted(yi)[:7], sorted(ji)[:7]

def format_weekday(d):
    return ["一","二","三","四","五","六","日"][d.weekday()]

# ─── Main ─────────────────────────────────────────────────
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
    weekday  = format_weekday(date_obj)
    terms    = get_solar_term(year, month, day)
    yi, ji   = get_yiji(terms)
    bazi     = get_bazi(year, month, day, hour, minute)

    if bazi:
        print("=" * 48)
        print(f"  📅 西元：{year} 年 {month} 月 {day} 日  星期{weekday}")
        print(f"  🎯 干支：{bazi['year']} 年 / {bazi['month']} 月 / {bazi['day']} 日 / {bazi['hour']} 時")
        print(f"  🐾 生肖：{bazi['zodiac']} 年")
        print(f"  🌿 節氣：{'、'.join(terms) if terms else '（無特殊節氣）'}")
        print(f"  📆 農曆：{bazi['lunar']}")
        print(f"  ✅ 宜：{'、'.join(yi)}")
        print(f"  ❌ 忌：{'、'.join(ji)}")
        print("=" * 48)
    else:
        print("錯誤：無法取得干支資訊，請確認 cantian-tymext 已正確安裝")

if __name__ == "__main__":
    main()
