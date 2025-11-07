# core/logger.py
import logging
import sys

# 포맷 정의
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

# 공통 포맷터
formatter = logging.Formatter(LOG_FORMAT)

# 콘솔 핸들러
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 파일 핸들러
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 루트 로거 설정
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)


def get_logger(name: str):
    """
    각 모듈에서 import해서 사용할 로거 반환
    """
    return logging.getLogger(name)