import sys
import subprocess

def run_tests():
    print("\n" + "=" * 50)
    print(" Teggy Smoke Test")
    print("=" * 50 + "\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode == 0:
        print("\n" + "=" * 50)
        print(" ✅ Все тесты пройдены")
        print("=" * 50)
        return 0
    else:
        print("\n" + "=" * 50)
        print(" ❌ Некоторые тесты не пройдены")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
