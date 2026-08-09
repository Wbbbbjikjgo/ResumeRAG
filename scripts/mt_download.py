"""多线程分段下载 BGE-M3 缺失文件（hf-mirror 支持 Range）。"""

import os
import sys
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

BASE = "https://hf-mirror.com/BAAI/bge-m3/resolve/main/"
DEST_DIR = r"models\models\BAAI--bge-m3\snapshots\master"
FILES = ["pytorch_model.bin", "tokenizer.json"]
NUM_THREADS = 8
CHUNK = 16 * 1024 * 1024  # 每段 16MB


def download_file(name: str) -> None:
    url = BASE + name
    dest = os.path.join(DEST_DIR, name)
    tmp = dest + ".parts"

    head = requests.head(url, allow_redirects=True, timeout=30)
    total = int(head.headers["Content-Length"])
    print(f"[{name}] total = {total/1e6:.1f} MB")

    if os.path.exists(dest) and os.path.getsize(dest) == total:
        print(f"[{name}] already complete")
        return

    # 分段
    ranges = []
    start = 0
    while start < total:
        end = min(start + CHUNK - 1, total - 1)
        ranges.append((start, end))
        start = end + 1

    os.makedirs(tmp, exist_ok=True)
    lock = threading.Lock()
    done_bytes = [0]

    def fetch_part(i: int, s: int, e: int) -> None:
        part_path = os.path.join(tmp, f"part_{i:05d}")
        # 已完成的分片跳过
        if os.path.exists(part_path) and os.path.getsize(part_path) == (e - s + 1):
            with lock:
                done_bytes[0] += (e - s + 1)
            return
        headers = {"Range": f"bytes={s}-{e}"}
        with requests.get(url, headers=headers, timeout=60, stream=True) as r:
            r.raise_for_status()
            with open(part_path, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)
        with lock:
            done_bytes[0] += (e - s + 1)
            if done_bytes[0] % (128 * 1024 * 1024) < CHUNK:
                print(f"[{name}] {done_bytes[0]/1e6:.0f}/{total/1e6:.0f} MB", flush=True)

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as pool:
        futures = [pool.submit(fetch_part, i, s, e) for i, (s, e) in enumerate(ranges)]
        for f in futures:
            f.result()

    # 合并
    print(f"[{name}] merging ...", flush=True)
    with open(dest, "wb") as out:
        for i in range(len(ranges)):
            part_path = os.path.join(tmp, f"part_{i:05d}")
            with open(part_path, "rb") as pf:
                while True:
                    buf = pf.read(8 * 1024 * 1024)
                    if not buf:
                        break
                    out.write(buf)
    assert os.path.getsize(dest) == total, f"size mismatch for {name}"
    print(f"[{name}] DONE", flush=True)


if __name__ == "__main__":
    for f in FILES:
        download_file(f)
    print("ALL FILES READY")
