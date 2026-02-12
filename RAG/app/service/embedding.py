from app.common.common import db_conn, ingest_chunk_file, chunk_dir
import os, time


def run_embedding():
    chunk_json = ['/content', '/summary']

    start = time.time()
    print(f'### [embedding] start')
    results = []
    for chunk in chunk_json:
        # SingleCollection + metadata filtering
        # collection name 지정
        db = db_conn('rag_test')
        full_chunk_dir = chunk_dir + chunk
        for fname in os.listdir(full_chunk_dir):
            if not fname.endswith('.json'):
                continue
            json_path = os.path.join(full_chunk_dir, fname)
            # metadata filtering 사용
            vector_type = "content" if "content" in chunk else "summary"
            ingest_chunk_file(json_path, db, vector_type)
            results.append(fname)
    end = time.time()
    elapsed = round(end - start, 2)
    print(f'### [embedding] end  총 걸린시간: {elapsed}초')
    return {"files": results, "elapsed_sec": elapsed}


if __name__ == "__main__":
    run_embedding()