from __future__ import annotations

import os
import shutil

from ..core.models import PreparedItem


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def copy_file_if_exists(src: str, dst_dir: str) -> str | None:
    if not src or not os.path.exists(src):
        return None
    ensure_dir(dst_dir)
    filename = os.path.basename(src)
    dst = os.path.join(dst_dir, filename)
    shutil.copy2(src, dst)
    return dst


def export_media_bundle(items: list[PreparedItem], audio_by_prompt: dict[str, dict[str, str]], media_dir: str) -> None:
    ensure_dir(media_dir)
    copied = 0
    missing: list[str] = []
    seen: set[str] = set()
    for item in items:
        audio = audio_by_prompt[item.prompt]
        for media_path in [audio["slow_path"], audio["normal_path"]]:
            basename = os.path.basename(media_path)
            if basename in seen:
                continue
            seen.add(basename)
            if os.path.exists(media_path):
                copy_file_if_exists(media_path, media_dir)
                copied += 1
            else:
                missing.append(media_path)
        if item.image:
            image_basename = os.path.basename(item.image)
            if image_basename not in seen:
                seen.add(image_basename)
                if os.path.exists(item.image):
                    copy_file_if_exists(item.image, media_dir)
                    copied += 1
                else:
                    missing.append(item.image)
    print(f"\n📦 Copied {copied} media files to: {media_dir}")
    if missing:
        print(f"⚠️ Missing media files: {len(missing)}")
        for path in missing[:20]:
            print(f"  - {path}")
        if len(missing) > 20:
            print("  - ...")
