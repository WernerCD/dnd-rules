"""Download the SRD rules text into source/ (run by hand when the sources change, not in CI).
    python tools/fetch_sources.py
2014: SRD 5.1 rule sections and conditions from 5e-bits/5e-database (MIT).
2024: SRD 5.2.1 chapters from downfallx/dnd-5e-srd-markdown; spells.md is cut to its rules part (before "Spell Descriptions")."""
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "source"
BITS = "https://raw.githubusercontent.com/5e-bits/5e-database/main/src/2014/en/"
MD = "https://raw.githubusercontent.com/downfallx/dnd-5e-srd-markdown/master/"
FILES = {
    "5ebits-2014-rule-sections.json": BITS + "5e-SRD-Rule-Sections.json",
    "5ebits-2014-conditions.json": BITS + "5e-SRD-Conditions.json",
    "srd52-rules-glossary.md": MD + "rules-glossary.md",
    "srd52-playing-the-game.md": MD + "playing-the-game.md",
    "srd52-gameplay-toolbox.md": MD + "gameplay-toolbox.md",
    "srd52-equipment.md": MD + "equipment.md",
    "srd52-spellcasting.md": MD + "spells.md",
}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dnd-rules-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")

OUT.mkdir(exist_ok=True)
for name, url in FILES.items():
    text = get(url)
    if name == "srd52-spellcasting.md":
        text = text.split("\n## Spell Descriptions")[0] + "\n"
    (OUT / name).write_text(text, encoding="utf-8", newline="\n")
    print(name, len(text))
