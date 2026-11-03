"""Builds build/preview/: a copy of this repo's content with the synthesized sounds wired in, to try
them in a debug build before anything is published. Serve it and point the app at it:

    python -P tools/audio/synth.py all --out build
    python -P tools/build_preview.py
    python -P -m http.server 8000 --bind 127.0.0.1 --directory build/preview

and put `contentBaseUrl=http://10.0.2.2:8000/` in the app's local.properties (emulator -> host).

Descriptions only describe the sound; they never say what listening to it will do for you.
"""

import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "preview"

# card id (keeps its image) -> (track file, title shown on the card, description)
TRACKS = {
    "sleep": ("velvet", "Kadife", "Yumuşak kahverengi gürültü, altında çok kısık bir akor."),
    "breathing": ("breath-tide", "Gelgit", "Yirmi dört saniyede bir kabarıp çekilen sıcak bir akor."),
    "focus": ("one-point", "Tek Nokta", "Tek bir re notası, tınısı yavaşça değişir."),
    "mindfulness": ("singing-bowl", "Ses Kasesi", "Yaklaşık yarım dakikada bir vurulan kase, sesi uzayıp söner."),
    "stress-relief": ("shoreline", "Kıyı", "Kabarıp köpüren, sonra geri çekilen dalgalar."),
    "chakra": ("wind-and-chimes", "Rüzgâr Çanı", "Esen rüzgâr ve arada küçük bir çan sesi."),
}
# extra cards that reuse another card's image: new id -> (image of, track, title, description)
EXTRA = {
    "night-rain": ("sleep", "night-rain", "Gece Yağmuru", "Çatıya yağan düzenli yağmur ve uzaktan bir uğultu."),
    "pink-haze": ("focus", "pink-haze", "Pembe Sis", "Pembe gürültü: dengeli, yumuşak bir hışırtı."),
}


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(ROOT, OUT, ignore=shutil.ignore_patterns(".git", "build", "tools", "__pycache__", "*.wav"))
    content = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
    by_id = {m["id"]: m for m in content["meditations"]}

    cards = []
    entries = [(cid, by_id[cid], *spec) for cid, spec in TRACKS.items()]
    entries += [(cid, by_id[image_of], *spec) for cid, (image_of, *spec) in EXTRA.items()]
    for cid, base, track, title, description in entries:
        # `label` is what the cards show, so it carries the track name; `title` is the detail heading.
        cards.append(dict(base, id=cid, label=title, title=title, description=description,
                          audio=f"audio/meditations/{track}.ogg"))
    content["meditations"] = cards
    (OUT / "content.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")

    audio = OUT / "audio" / "meditations"
    for old in audio.glob("*"):
        old.unlink()
    for card in cards:
        name = card["audio"].split("/")[-1]
        shutil.copy(ROOT / "build" / name, audio / name)
    print(f"{OUT}: {len(cards)} cards, {sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file()) // 1000} KB")


if __name__ == "__main__":
    main()
