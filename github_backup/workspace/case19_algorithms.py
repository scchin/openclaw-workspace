
import unittest

def get_fibonacci(n):
    """
    計算第 n 個費氏數列 (Fibonacci sequence)
    定義: F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def get_nth_prime(n):
    """
    計算第 n 個質數 (Prime number)
    """
    if n <= 0:
        return None
    
    primes = []
    candidate = 2
    while len(primes) < n:
        is_prime = True
        # 只需要檢查到 candidate 的平方根
        for p in primes:
            if p * p > candidate:
                break
            if candidate % p == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
        candidate += 1
    return primes[-1]

class TestCase19(unittest.TestCase):
    def test_fibonacci_19(self):
        # F(19) = 4181
        self.assertEqual(get_fibonacci(19), 4181)
        print(f"第 19 個費氏數列: {get_fibonacci(19)}")

    def test_prime_19(self):
        # 質數序列: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67
        self.assertEqual(get_nth_prime(19), 67)
        print(f"第 19 個質數: {get_nth_prime(19)}")

if __name__ == "__main__":
    # 執行測試並打印結果
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCase19)
    unittest.TextTestRunner(verbosity=2).run(suite)
