import sys
import os

print("--- 1. 현재 파이썬 실행 파일 경로 ---")
print(sys.executable)
print("-" * 40)

print("\n--- 2. 파이썬이 모듈을 찾는 경로 (sys.path) ---")
# venv의 site-packages 경로가 이 목록에 있어야 합니다.
# 예: C:\...\AGENT\venv\Lib\site-packages
for path in sys.path:
    print(path)
print("-" * 40)

# venv의 site-packages 경로를 강제로 확인
venv_site_packages = os.path.join(os.path.dirname(sys.executable), '..', 'Lib', 'site-packages')
print(f"\n--- 3. venv의 'site-packages' 경로 확인 ---")
print(f"예상 경로: {venv_site_packages}")
print(f"이 경로가 실제로 존재합니까? {os.path.exists(venv_site_packages)}")
print("-" * 40)

print(f"\n--- 4. 'langchain' 패키지가 site-packages에 있습니까? ---")
langchain_path = os.path.join(venv_site_packages, 'langchain')
print(f"예상 경로: {langchain_path}")
print(f"이 경로가 실제로 존재합니까? {os.path.exists(langchain_path)}")
print("-" * 40)


print("\n--- 5. 임포트 테스트 ---")
try:
    from langchain.chains import LLMChain
    print("SUCCESS: 'from langchain.chains import LLMChain' 성공!")
except ModuleNotFoundError as e:
    print(f"ERROR: 임포트 실패. 오류 메시지: {e}")
except Exception as e:
    print(f"OTHER ERROR: {e}")
print("-" * 40)