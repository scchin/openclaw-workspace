import re
from deep_translator import GoogleTranslator

def translate_to_zh(text: str) -> str:
    if not text: return ""
    try:
        # Only translate if it contains English/Non-Chinese characters to save API calls
        if re.search(r'[a-zA-Z]', text):
            return GoogleTranslator(source='auto', target='zh-TW').translate(text)
        return text
    except Exception as e:
        import sys
        print(f"[Translation Error] {e}", file=sys.stderr)
        return text
