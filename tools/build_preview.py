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

# card id (keeps its image) -> (track file, title, description); text is {language: text}
TRACKS = {
    "sleep": ("velvet",
              {"tr": "Kadife", "en": "Velvet"},
              {"tr": "Yumuşak kahverengi gürültü, altında çok kısık bir akor.",
               "en": "Soft brown noise over a very quiet chord."}),
    "breathing": ("breath-tide",
                  {"tr": "Gelgit", "en": "Tide"},
                  {"tr": "Yirmi dört saniyede bir kabarıp çekilen sıcak bir akor.",
                   "en": "A warm chord that rises and ebbs every twenty-four seconds."}),
    "focus": ("one-point",
              {"tr": "Tek Nokta", "en": "One Point"},
              {"tr": "Tek bir re notası, tınısı yavaşça değişir.",
               "en": "A single held D, its tone shifting slowly."}),
    "mindfulness": ("singing-bowl",
                    {"tr": "Ses Kasesi", "en": "Singing Bowl"},
                    {"tr": "Yaklaşık yarım dakikada bir vurulan kase, sesi uzayıp söner.",
                     "en": "A bowl struck about every half minute, ringing out into silence."}),
    "stress-relief": ("shoreline",
                      {"tr": "Kıyı", "en": "Shoreline"},
                      {"tr": "Kabarıp köpüren, sonra geri çekilen dalgalar.",
                       "en": "Waves that build, foam and draw back."}),
    "chakra": ("wind-and-chimes",
               {"tr": "Rüzgâr Çanı", "en": "Wind Chimes"},
               {"tr": "Esen rüzgâr ve arada küçük bir çan sesi.",
                "en": "Gusting wind with a small chime now and then."}),
}
# extra cards that reuse another card's image: new id -> (image of, track, title, description)
EXTRA = {
    "night-rain": ("sleep", "night-rain",
                   {"tr": "Gece Yağmuru", "en": "Night Rain"},
                   {"tr": "Çatıya yağan düzenli yağmur ve uzaktan bir uğultu.",
                    "en": "Steady rain on a roof and a distant low rumble."}),
    "pink-haze": ("focus", "pink-haze",
                  {"tr": "Pembe Sis", "en": "Pink Haze"},
                  {"tr": "Pembe gürültü: dengeli, yumuşak bir hışırtı.",
                   "en": "Pink noise: an even, soft hiss."}),
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
