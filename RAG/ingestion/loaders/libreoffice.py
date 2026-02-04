from pathlib import Path
import subprocess
import shutil

def convert_docs_in_dir(raw_dir: str,staging_dir: str, converted_dir: str):
    raw_dir = Path(raw_dir).resolve()
    staging_dir = Path(staging_dir).resolve()
    converted_dir = Path(converted_dir).resolve()
    converted_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "copied": [],
        "converted": [],
        "skipped": [],
        "failed": []
    }

    # 1. raw → staging 복사
    for src in raw_dir.iterdir():
        if not src.is_file():
            continue

        dst = staging_dir / src.name
        if dst.exists():
            continue  # 이미 있으면 재복사 안 함

        shutil.copy(src, dst)
        results["copied"].append(src.name)

    # 2. staging 디렉토리 기준 변환
    for src in staging_dir.iterdir():
        if not src.is_file():
            continue

        ext = src.suffix.lower()

        try:
            # 이미 PDF → 그대로 복사
            if ext == ".pdf":
                dst = converted_dir / src.name
                shutil.copy(src, dst) # staging -> converted

                src.unlink() # staging 삭제 

                results["skipped"].append(src.name)

            # HWP → staging 보류 (ahk로 pdf 변환 예정)
            else:
                results["skipped"].append(src.name)

        except Exception:
            results["failed"].append(src.name)

    return results
