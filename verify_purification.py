import subprocess

def test():
    with open('test_leak.txt', 'w', encoding='utf-8') as f:
        f.write('分析結果：請求量 \\rightarrow 增加，導致延遲 $\\approx$ 200ms，且效能 $\\downarrow$ 10%。\\text{結論：系統不穩定。} 此外，$\\alpha$ 參數導致 $\\beta$ 偏移。')
    
    result = subprocess.run(['python3', '/Users/KS/.openclaw/workspace/purify_output.py', '--file', 'test_leak.txt'], capture_output=True, text=True, encoding='utf-8')
    print(result.stdout)

if __name__ == "__main__":
    test()
