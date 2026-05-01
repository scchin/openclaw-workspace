
def get_nth_prime(n):
    """計算第 n 個質數"""
    if n < 1:
        return None
    
    def is_prime(num):
        if num < 2:
            return False
        for i in range(2, int(num**0.5) + 1):
            if num % i == 0:
                return False
        return True

    count = 0
    candidate = 1
    while count < n:
        candidate += 1
        if is_prime(candidate):
            count += 1
    return candidate

def get_nth_fibonacci(n):
    """計算第 n 個費氏數列 (F0=0, F1=1, F2=1, ...)"""
    if n < 0:
        return None
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def test_algorithms():
    # 測試質數
    # 1: 2, 2: 3, 3: 5, 4: 7, 5: 11
    assert get_nth_prime(1) == 2
    assert get_nth_prime(5) == 11
    prime_53 = get_nth_prime(53)
    print(f"第 53 個質數是: {prime_53}")

    # 測試費氏數列
    # F0=0, F1=1, F2=1, F3=2, F4=3, F5=5
    assert get_nth_fibonacci(0) == 0
    assert get_nth_fibonacci(1) == 1
    assert get_nth_fibonacci(5) == 5
    fib_53 = get_nth_fibonacci(53)
    print(f"第 53 個費氏數列是: {fib_53}")

    print("所有測試用例通過！")

if __name__ == "__main__":
    test_algorithms()
