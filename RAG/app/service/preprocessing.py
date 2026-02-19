from app.common.common import chunk_file, converted_dir
import os, time


# preprocessing 실행
def run_preprocessing(converted_dir: str):

    # 시작 시간
    start = time.time()
    print(f'### [preprocessing] start')

    for name in os.listdir(converted_dir):
        if '.' not in name:
            continue

        chunk_file(converted_dir + '/' + name)
        print(f'### {converted_dir}/{name}')

    print(f'### [preprocessing] end')
    # 종료 시간
    end = time.time()
    print(f'### [preprocessing] 총 걸린시간: {end-start}초')


if __name__ == "__main__":
    run_preprocessing(converted_dir)