import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from anki_deck_builder.audio.cache import audio_cache_paths, ensure_cache_dirs
from anki_deck_builder.domain.models import AudioBundle, StudyItem


class AudioService:
    def __init__(self, synthesizer, workers: int):
        self.synthesizer = synthesizer
        self.workers = workers

    def ensure_audio_for_items(self, items: list[StudyItem], voice_id: str, required_modes: tuple[str, ...]) -> tuple[dict[str, AudioBundle], int, int]:
        ensure_cache_dirs()
        bundles: dict[str, AudioBundle] = {}
        futures = []
        total_chars = 0
        rows_regenerated = 0

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            for item in items:
                paths = audio_cache_paths(item.prompt, voice_id)
                bundle = AudioBundle(
                    key=paths["key"],
                    slow=paths["slow"],
                    normal=paths["normal"],
                )
                bundles[item.prompt] = bundle

                needs_regen = False

                if "slow" in required_modes and not os.path.exists(bundle.slow):
                    futures.append(
                        executor.submit(
                            self.synthesizer.synthesize_slow,
                            item.prompt,
                            bundle.slow,
                            voice_id,
                        )
                    )
                    needs_regen = True

                if "normal" in required_modes and not os.path.exists(bundle.normal):
                    futures.append(
                        executor.submit(
                            self.synthesizer.synthesize_normal,
                            item.prompt,
                            bundle.normal,
                            voice_id,
                        )
                    )
                    needs_regen = True

                if needs_regen:
                    rows_regenerated += 1
                    total_chars += len(item.prompt) * len(required_modes)

            for future in tqdm(as_completed(futures), total=len(futures), desc="Audio"):
                future.result()

        return bundles, total_chars, rows_regenerated
