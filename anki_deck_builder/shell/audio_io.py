from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from tqdm import tqdm


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def escape_ssml_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def synthesize_to_file(client, text: str, filename: str, voice_id: str, slow: bool) -> str | None:
    ensure_dir(os.path.dirname(filename))
    try:
        if slow:
            ssml = f"<speak><prosody rate='70%'>{escape_ssml_text(text)}</prosody></speak>"
            response = client.synthesize_speech(
                Text=ssml,
                TextType="ssml",
                OutputFormat="mp3",
                VoiceId=voice_id,
            )
        else:
            response = client.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId=voice_id,
            )
        with open(filename, "wb") as f:
            f.write(response["AudioStream"].read())
        return filename
    except Exception as exc:
        print(f"\n❌ Error generating {filename}: {exc}")
        return None


def realize_audio_requests(audio_requests: list[dict], workers: int) -> list[dict]:
    client = boto3.client("polly", region_name="us-east-1")
    futures = []
    total_chars = 0
    items_regenerated = 0

    print(f"\n🔊 Processing audio with {workers} workers...\n")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for req in audio_requests:
            item_regenerated = False
            for part in req.get("audio_parts", {}).values():
                slow_exists = os.path.exists(part["slow_path"])
                normal_exists = os.path.exists(part["normal_path"])
                if slow_exists and normal_exists:
                    continue
                if not item_regenerated:
                    items_regenerated += 1
                    item_regenerated = True
                total_chars += len(part["text"]) * 2
                if not slow_exists:
                    futures.append(executor.submit(synthesize_to_file, client, part["text"], part["slow_path"], req["voice_id"], True))
                if not normal_exists:
                    futures.append(executor.submit(synthesize_to_file, client, part["text"], part["normal_path"], req["voice_id"], False))

        for future in tqdm(as_completed(futures), total=len(futures), desc="Audio"):
            future.result()

    cost_usd = total_chars * 16 / 1_000_000
    print(f"\n💰 Estimated AWS Polly cost for this run: ${cost_usd:.4f} USD")
    print(f"🔁 Items with regenerated audio: {items_regenerated}")
    return audio_requests
