from typing import Optional

import boto3


def escape_ssml_text(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


class PollySynthesizer:
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client("polly", region_name=region_name)

    def synthesize_normal(self, text: str, filename: str, voice_id: str) -> Optional[str]:
        try:
            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId=voice_id,
            )
            with open(filename, "wb") as f:
                f.write(response["AudioStream"].read())
            return filename
        except Exception as e:
            print(f"\n❌ Error generating {filename}: {e}")
            return None

    def synthesize_slow(self, text: str, filename: str, voice_id: str) -> Optional[str]:
        try:
            ssml = f"<speak><prosody rate='70%'>{escape_ssml_text(text)}</prosody></speak>"
            response = self.client.synthesize_speech(
                Text=ssml,
                TextType="ssml",
                OutputFormat="mp3",
                VoiceId=voice_id,
            )
            with open(filename, "wb") as f:
                f.write(response["AudioStream"].read())
            return filename
        except Exception as e:
            print(f"\n❌ Error generating {filename}: {e}")
            return None
