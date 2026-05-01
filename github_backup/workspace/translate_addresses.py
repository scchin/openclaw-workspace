import sys
from deep_translator import GoogleTranslator
import re

def translate_to_zh(text: str) -> str:
    if not text: return ""
    try:
        if re.search(r'[a-zA-Z]', text):
            return GoogleTranslator(source='auto', target='zh-TW').translate(text)
        return text
    except Exception as e:
        return text

addresses = [
    "No. 54號, Lane 4, Section 2, Changping Rd, Beitun District, Taichung City, 406",
    "406, Taichung City, Beitun District, 敦富二街93號",
    "No. 288號, Jingxian Rd, Beitun District, Taichung City, 406",
    "No. 65號, Section 1, Songzhuwu Rd, Beitun District, Taichung City, 406",
    "No. 220號, Section 2, Rehe Rd, Beitun District, Taichung City, 406"
]

for addr in addresses:
    print(f"{addr} | {translate_to_zh(addr)}")
