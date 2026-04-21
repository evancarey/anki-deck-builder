import os
import shutil


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def copy_file_if_exists(src: str, dst_dir: str):
    if not src or not os.path.exists(src):
        return None
    ensure_dir(dst_dir)
    filename = os.path.basename(src)
    dst = os.path.join(dst_dir, filename)
    shutil.copy2(src, dst)
    return dst
