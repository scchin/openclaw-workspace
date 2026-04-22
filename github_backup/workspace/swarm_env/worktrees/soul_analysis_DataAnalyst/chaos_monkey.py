import subprocess
import time
import requests
import os

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def check_process(name):
    try:
        subprocess.check_output(["pgrep", "-f", name])
        return True
    except subprocess.CalledProcessError:
        return False

def run_test():
    results = {}

    # Test 1: Persistence (Kill & Recover)
    log("Running Test 1: Persistence...")
    targets = ["injection_proxy.py", "sync_sidecar.py"]
    recovery_times = []
    
    for target in targets:
        subprocess.run(["pkill", "-9", "-f", target])
        start = time.time()
        while not check_process(target):
            time.sleep(0.1)
        end = time.time()
        recovery_times.append(end - start)
        log(f"Target {target} recovered in {end-start:.3f}s")
    
    time.sleep(1) # Crucial: give servers time to bind to ports
    results['persistence'] = {
        'status': 'PASS',
        'avg_recovery': sum(recovery_times)/len(recovery_times)
    }

    # Test 2: Refresh Bombing
    log("Running Test 2: Refresh Bombing...")
    try:
        start = time.time()
        for i in range(50):
            requests.get("http://127.0.0.1:18793/trigger-refresh", timeout=1)
        end = time.time()
        results['refresh_bombing'] = {'status': 'PASS', 'duration': end-start, 'count': 50}
        log("Refresh bombing completed without crash.")
    except Exception as e:
        results['refresh_bombing'] = {'status': 'FAIL', 'error': str(e)}
        log(f"Refresh bombing failed: {e}")

    # Test 3: Auth Bypass (18792 accessibility)
    log("Running Test 3: Auth Bypass...")
    try:
        resp = requests.get("http://127.0.0.1:18792", timeout=2)
        if resp.status_code == 200:
            results['auth_bypass'] = {'status': 'PASS'}
            log("Auth bypass confirmed.")
        else:
            results['auth_bypass'] = {'status': 'FAIL', 'code': resp.status_code}
    except Exception as e:
        results['auth_bypass'] = {'status': 'FAIL', 'error': str(e)}

    return results

if __name__ == "__main__":
    res = run_test()
    print("\n--- FINAL RESULTS ---")
    print(res)
