# D&D Rules Reference

A fast, searchable rules quick reference for the table, for 2014 and 2024 D&D 5e rules, with what changed between them.

**Live:** https://wernercd.github.io/dnd-rules/ · part of the [D&D Toolbox](https://wernercd.github.io/dnd/) · [Changes](https://wernercd.github.io/dnd-rules/changes.html)

## Features
- All 15 conditions (including the reworked 2024 Exhaustion), the actions, bonus actions, reactions, opportunity attacks, two-weapon fighting and Light weapons, grapple and shove, cover, mounted combat.
- Resistance, vulnerability and immunity (stacking and the order modifiers apply in), dropping to 0 HP and death saves, knocking out, temporary hit points, short and long rests.
- Concentration, casting time and the bonus action spell rule, spell components, vision and light, hiding and unseen attackers, travel pace, falling and suffocating.
- A 2014 / 2024 switch (it follows the active D&D Toolbox character), a "what changed in 2024" note on every topic that differs, and **Compare editions** to read both side by side.
- Search across every topic's title, summary and full text, category chips, "Changed in 2024" filter, a topic list on wide screens.
- Every topic has a stable link (`#prone`, `#grapple-shove`, `#casting-time` ...); conditions named in the text link to their card.
- Print layout: collapsed topics print as their summary, expanded ones with full text.

## Data and copyright
The rules text is from the System Reference Documents: SRD 5.1 for 2014 (taken from the [5e-bits database](https://github.com/5e-bits/5e-database)) and SRD 5.2.1 for 2024 (taken from [a Markdown conversion](https://github.com/downfallx/dnd-5e-srd-markdown)). The copies used are in `source/`. The one-line summaries, keywords and "what changed" notes in `tools/build_data.py` are original. Nothing from outside the SRDs is included, and nothing comes from D&D Beyond.

## Layout
| Path | What |
|---|---|
| `site/` | The static site (no build step for the page itself); `site/rules.js` is generated |
| `source/` | The SRD text the data is built from |
| `tools/build_data.py` | Builds `site/rules.js`: the topic list, which SRD sections each topic uses, summaries and change notes |
| `tools/fetch_sources.py` | Re-downloads `source/` (by hand, not in CI) |
| `tools/check_site.py` | The shared D&D Toolbox smoke check |

## Run locally
```bash
python tools/build_data.py
python -m http.server 8765 --directory site
```
Checks (CI runs the same before every deploy): `python tools/build_data.py && python tools/check_site.py`.

## Credits and license
- Code: MIT, see [LICENSE](LICENSE).
- This work includes material from the System Reference Document 5.1 and 5.2 by Wizards of the Coast LLC, available at https://dnd.wizards.com/resources/systems-reference-document, licensed under the Creative Commons Attribution 4.0 International License (https://creativecommons.org/licenses/by/4.0/legalcode).
- Unofficial fan content. Not affiliated with or endorsed by Wizards of the Coast.
