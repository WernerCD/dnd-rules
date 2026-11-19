"""Build site/rules.js (window.RULES) from the SRD text in source/.

    python tools/build_data.py

Sources (downloaded by tools/fetch_sources.py, committed in source/):
  2014 (SRD 5.1): 5ebits-2014-rule-sections.json, 5ebits-2014-conditions.json  (5e-bits/5e-database, MIT)
  2024 (SRD 5.2.1): srd52-*.md                                                 (downfallx/dnd-5e-srd-markdown)
The rules text itself is SRD 5.1 / 5.2.1, CC BY 4.0. The summaries, keywords and "what changed" notes in
TOPICS below are original text written for this site.
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source"
OUT = ROOT / "site" / "rules.js"

# ---------------------------------------------------------------- sources
B14 = {x["index"]: x["desc"] for x in json.loads((SRC / "5ebits-2014-rule-sections.json").read_text(encoding="utf-8"))}
C14 = {x["index"]: x["desc"] for x in json.loads((SRC / "5ebits-2014-conditions.json").read_text(encoding="utf-8"))}
MD = {k: (SRC / f"srd52-{v}.md").read_text(encoding="utf-8") for k, v in
      {"G": "rules-glossary", "P": "playing-the-game", "T": "gameplay-toolbox", "E": "equipment", "S": "spellcasting"}.items()}

HEAD = re.compile(r"^(#{1,6})\s*(.+?)\s*$")

def norm(t):
    return re.sub(r"\s*\[[^\]]*\]$", "", t.strip()).lower()

def section(lines, title):
    """lines of the section headed `title` (heading line included), up to the next heading of the same or higher level."""
    for i, ln in enumerate(lines):
        m = HEAD.match(ln)
        if m and norm(m.group(2)) == norm(title):
            lvl = len(m.group(1)); out = [ln]
            for ln2 in lines[i + 1:]:
                m2 = HEAD.match(ln2)
                if m2 and len(m2.group(1)) <= lvl: break
                out.append(ln2)
            return out
    raise KeyError(title)

def cut(lines, stop=(), drop=()):
    """stop: truncate at the first of these subheadings. drop: remove these subsections."""
    out, skip = [], None
    for ln in lines[1:] if lines and HEAD.match(lines[0]) else lines:
        m = HEAD.match(ln)
        if m:
            if norm(m.group(2)) in [norm(s) for s in stop]: break
            if skip is not None and len(m.group(1)) <= skip: skip = None
            if norm(m.group(2)) in [norm(s) for s in drop]: skip = len(m.group(1)); continue
        if skip is None: out.append(ln)
    return out

def part(spec):
    """spec = (doc, path, opts). doc: 'B' (2014 section index first in path), 'C' (2014 condition), or a 2024 md key."""
    doc, path, opts = spec[0], spec[1], (spec[2] if len(spec) > 2 else {})
    if isinstance(path, str): path = [path]
    if doc == "C":
        return fmt_c14(path[0])
    if doc == "B":
        lines = B14[path[0]].splitlines(); path = path[1:]
    else:
        lines = MD[doc].splitlines()
    for t in path: lines = section(lines, t)
    head = HEAD.match(lines[0]).group(2) if lines and HEAD.match(lines[0]) else None
    body = cut(lines, opts.get("stop", ()), opts.get("drop", ()))
    return render(body, opts.get("label", None), head)

def fmt_c14(key):
    rows, md = [], []
    for ln in C14[key]:
        m = re.match(r"^(\d) - (.+)$", ln)
        if m: rows.append(m.groups()); continue
        if rows:
            md.append("| Level | Effect |"); md.append("|---|---|")
            md += [f"| {a} | {b} |" for a, b in rows]; md.append(""); rows = []
        md.append(ln); md.append("")
    return render(md, None, None)

# ---------------------------------------------------------------- markdown -> html (small, for this text only)
def inline(t):
    t = html.escape(t, quote=False)
    t = t.replace("---", "—").replace("--", "—")
    t = re.sub(r"srd:([a-z-]+)", lambda m: "<i>" + m.group(1).replace("-", " ").title() + "</i>", t)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"(?<![\w])_(?=\S)(.+?)(?<=\S)_(?![\w])", r"<i>\1</i>", t)
    t = t.replace("</b> <b>", " ")
    return t

def clean(t):
    t = re.sub(r"\s*\((?:see|as explained in) (?:the )?appendix[^)]*\)", "", t, flags=re.I)
    for w in DASHED: t = t.replace(w, w.replace("-", "—"))
    t = re.sub(r"(\w+) \(see the condition\)", r"\1", t)
    t = re.sub(r"\s*_See also_ .*$", "", t)            # cross-references to book chapters; the site adds its own links
    return t

# SRD 5.1 text (5e-bits) writes some em dashes as a plain hyphen
DASHED = ["components-or", "focus-but", "hidden-both", "unheard-when", "activity-at", "activity-the", "rest-time",
          "area-such", "foliage-blocks"]

def table_html(rows, head_rows=1):
    out = ['<div class="tbl"><table>']
    for i, r in enumerate(rows):
        tag = "th" if i < head_rows else "td"
        out.append("<tr>" + "".join(f"<{tag}>{inline(c.strip())}</{tag}>" for c in r) + "</tr>")
    out.append("</table></div>")
    return "".join(out)

def render(lines, label, head):
    out, para, lst, i = [], [], None, 0
    def flush():
        nonlocal para, lst
        if para:
            p = clean(" ".join(s.strip() for s in para)).strip()
            if p: out.append(f"<p>{inline(p)}</p>")
            para = []
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{inline(clean(x))}</li>" for x in items) + f"</{tag}>"); lst = None
    if label: out.append(f'<h4 class="part-h">{html.escape(label)}</h4>')
    while i < len(lines):
        ln = lines[i]
        m = HEAD.match(ln)
        if m:
            flush(); out.append("<h5>" + inline(re.sub(r"\s*\[[^\]]*\]$", "", m.group(2))) + "</h5>"); i += 1; continue
        s = ln.strip()
        if s.startswith("<table"):
            flush(); j = i; buf = []
            while j < len(lines):
                buf.append(lines[j]); j += 1
                if "</table>" in lines[j - 1]: break
            raw = "\n".join(buf)
            rows = [[re.sub(r"<[^>]+>", "", c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
                    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.S)]
            out.append(table_html(rows, len(re.findall(r"<tr", raw.split("<tbody")[0])) if "<thead" in raw else 1))
            i = j; continue
        if s.startswith("|"):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = lines[i].strip().strip("|").split("|")
                if not all(re.fullmatch(r"\s*:?-+:?\s*", c) for c in cells): rows.append(cells)
                i += 1
            out.append(table_html(rows)); continue
        if s.startswith(">"):
            flush(); buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            out.append('<aside class="side">' + render(buf, None, None) + "</aside>"); continue
        mli = re.match(r"^\s*(?:[-*]|(\d+)\.)\s+(.*)$", ln)
        if mli:
            tag = "ol" if mli.group(1) else "ul"
            if para: flush()
            if lst and lst[0] != tag: flush()
            if not lst: lst = (tag, [])
            lst[1].append(mli.group(2)); i += 1; continue
        if not s:
            flush(); i += 1; continue
        if lst and not para:                 # continuation of a list item
            lst[1][-1] += " " + s; i += 1; continue
        para.append(ln); i += 1
    flush()
    return "".join(out)

CONDS = ["blinded", "charmed", "deafened", "exhaustion", "frightened", "grappled", "incapacitated", "invisible",
         "paralyzed", "petrified", "poisoned", "prone", "restrained", "stunned", "unconscious"]

def crosslink(h, self_id):
    """link 'the Prone condition' / 'grappled condition' to that condition's card (outside tags and headings)."""
    def sub(m):
        w = m.group(1)
        return m.group(0) if w.lower() == self_id else f'<a href="#{w.lower()}" class="xref">{w}</a>{m.group(2)}'
    parts = re.split(r"(<h[45][^>]*>.*?</h[45]>|<[^>]+>)", h)
    rx = re.compile(r"\b(" + "|".join(CONDS) + r")( condition)", re.I)
    return "".join(p if p.startswith("<") else rx.sub(sub, p) for p in parts)

def ed(specs, self_id):
    if isinstance(specs, str):
        return {"none": specs}
    if not isinstance(specs, list): specs = [specs]
    return {"html": crosslink("".join(part(s) for s in specs), self_id)}

# ---------------------------------------------------------------- topics
# cat: cond, act, combat, dmg, spell, explore
# sum: one-line summary (original). chg: what changed 2014 -> 2024 (original), or None when the rule is the same.
TOPICS = []
def T(id, title, cat, sum, e14, e24, chg=None, kw="", rel=()):
    TOPICS.append({"id": id, "title": title, "cat": cat, "sum": sum, "chg": chg, "kw": kw, "rel": list(rel),
                   "e14": e14, "e24": e24})

def G(name, **o): return ("G", name, o)

# ---- conditions
T("blinded", "Blinded", "cond", "You can't see. Attacks against you have advantage; your attacks have disadvantage.",
  ("C", "blinded"), G("Blinded [Condition]"), kw="blind sight darkness")
T("charmed", "Charmed", "cond", "You can't attack or harmfully target the charmer, and it has advantage on social checks with you.",
  ("C", "charmed"), G("Charmed [Condition]"), kw="charm")
T("deafened", "Deafened", "cond", "You can't hear and automatically fail checks that rely on hearing.",
  ("C", "deafened"), G("Deafened [Condition]"), kw="deaf hearing")
T("exhaustion", "Exhaustion", "cond", "Stacking levels of fatigue. Level 6 is death; a long rest removes one level.",
  ("C", "exhaustion"), G("Exhaustion [Condition]"),
  chg="Completely reworked. 2014 has a six-step table of separate penalties (disadvantage on checks, speed halved, and so on). "
      "In 2024 every level simply takes 2 off every D20 Test (attack rolls, ability checks and saving throws) and 5 feet off your Speed. "
      "Level 6 is still death, and a long rest still removes one level (2014 also needs food and drink).",
  kw="tired fatigue levels starvation forced march", rel=["resting", "suffocating", "travel-pace"])
T("frightened", "Frightened", "cond", "Disadvantage on checks and attacks while you can see the source of your fear, and you can't move closer to it.",
  ("C", "frightened"), G("Frightened [Condition]"), kw="fear scared")
T("grappled", "Grappled", "cond", "Your Speed is 0. It ends if the grappler is incapacitated or you're moved out of its reach.",
  ("C", "grappled"), G("Grappled [Condition]"),
  chg="2024 adds two effects: you have disadvantage on attack rolls against anyone other than the grappler, and the grappler can move you "
      "with it (each foot costs it an extra foot unless you are Tiny or two or more sizes smaller). Escaping is a check against the grapple's escape DC instead of a contest.",
  kw="grab hold", rel=["grapple-shove"])
T("incapacitated", "Incapacitated", "cond", "You can't take actions or reactions.",
  ("C", "incapacitated"), G("Incapacitated [Condition]"),
  chg="2024 makes it harsher: no bonus actions either, your Concentration breaks, you can't speak, and you have disadvantage on Initiative. "
      "Paralyzed, Petrified, Stunned and Unconscious all include it, so they change too.",
  kw="helpless", rel=["concentration"])
T("invisible", "Invisible", "cond", "Others can't see you without magic or a special sense; your attacks have advantage, attacks against you have disadvantage.",
  ("C", "invisible"), G("Invisible [Condition]"),
  chg="2024 adds advantage on Initiative, and says effects that need to see their target don't affect you unless the effect's creator can see you. "
      "A successful Hide action now gives you this condition.",
  kw="unseen invisibility", rel=["hiding"])
T("paralyzed", "Paralyzed", "cond", "Incapacitated and can't move or speak. You fail Str and Dex saves; hits from within 5 feet are critical hits.",
  ("C", "paralyzed"), G("Paralyzed [Condition]"), kw="paralysis hold person", rel=["incapacitated"])
T("petrified", "Petrified", "cond", "Turned to stone: incapacitated, unaware, resistant to all damage and immune to poison and disease.",
  ("C", "petrified"), G("Petrified [Condition]"), kw="stone flesh to stone", rel=["incapacitated"])
T("poisoned", "Poisoned", "cond", "Disadvantage on attack rolls and ability checks.",
  ("C", "poisoned"), G("Poisoned [Condition]"), kw="poison")
T("prone", "Prone", "cond", "You can only crawl or spend half your movement to stand. Melee attackers within 5 feet have advantage; ranged attackers have disadvantage.",
  ("C", "prone"), G("Prone [Condition]"), kw="knocked down lying stand up crawl", rel=["grapple-shove", "falling"])
T("restrained", "Restrained", "cond", "Speed 0, disadvantage on your attacks and Dex saves, and attacks against you have advantage.",
  ("C", "restrained"), G("Restrained [Condition]"), kw="web net entangle")
T("stunned", "Stunned", "cond", "Incapacitated; you automatically fail Str and Dex saves and attacks against you have advantage.",
  ("C", "stunned"), G("Stunned [Condition]"),
  chg="2014 also says you can't move and can speak only falteringly. 2024 drops both, so a stunned creature keeps its Speed, "
      "though the 2024 Incapacitated condition still takes away actions, bonus actions, reactions and speech.",
  kw="stun stunning strike", rel=["incapacitated"])
T("unconscious", "Unconscious", "cond", "Incapacitated, prone and unaware. You drop what you hold, fail Str and Dex saves, and hits from within 5 feet are critical hits.",
  ("C", "unconscious"), G("Unconscious [Condition]"), kw="asleep knocked out dying", rel=["death-saves", "knock-out"])

# ---- actions
T("actions", "Actions in combat", "act", "The main things you can do with your action on your turn.",
  ("B", ["actions-in-combat", "Actions in Combat"], {"stop": ["Attack"]}),
  [("P", "Actions", {"stop": ["One Thing at a Time"]}), ("P", ["Actions", "One Thing at a Time"], {"label": "One Thing at a Time"})],
  chg="The list changed. Cast a Spell became <b>Magic</b> (which also covers magic items and magical features), Use an Object became <b>Utilize</b>, "
      "and <b>Influence</b> and <b>Study</b> are new. Search and Study name the skills they use.",
  kw="action list what can I do", rel=["your-turn", "bonus-actions", "reactions"])
T("attack", "Attack", "act", "Make one melee or ranged attack (more with Extra Attack).",
  ("B", ["actions-in-combat", "Attack"]), G("Attack [Action]"),
  chg="2024 lets you equip or unequip one weapon as part of each attack you make with this action, and lists the Unarmed Strike as an option.",
  kw="extra attack weapon draw sheathe", rel=["opportunity-attacks", "two-weapon", "grapple-shove"])
T("dash", "Dash", "act", "Gain extra movement equal to your Speed for this turn.",
  ("B", ["actions-in-combat", "Dash"]), G("Dash [Action]"), kw="run move speed double")
T("disengage", "Disengage", "act", "Your movement doesn't provoke opportunity attacks for the rest of the turn.",
  ("B", ["actions-in-combat", "Disengage"]), G("Disengage [Action]"), kw="retreat withdraw", rel=["opportunity-attacks"])
T("dodge", "Dodge", "act", "Until your next turn, attacks against you have disadvantage and you have advantage on Dex saves.",
  ("B", ["actions-in-combat", "Dodge"]), G("Dodge [Action]"), kw="defend")
T("help", "Help", "act", "Give an ally advantage on a check or on an attack against a nearby enemy.",
  ("B", ["actions-in-combat", "Help"]),
  [G("Help [Action]"), ("P", ["Damage and Healing", "Stabilizing a Character"], {"label": "Stabilizing a Character"})],
  chg="To help with an ability check in 2024 you need proficiency in a skill or tool that applies. Helping an attack works the same way. "
      "Help also covers first aid: you take the Help action to stabilize a creature at 0 Hit Points with a DC 10 Wisdom (Medicine) check. In 2014 that is the same check, made with your action but not as Help.",
  kw="aid assist first aid advantage", rel=["death-saves"])
T("ready", "Ready", "act", "Choose a trigger and an action; when the trigger happens, act with your reaction.",
  ("B", ["actions-in-combat", "Ready"]), G("Ready [Action]"), kw="readied hold action trigger", rel=["reactions", "concentration"])
T("search", "Search", "act", "Look for something: usually a Wisdom (Perception) check.",
  ("B", ["actions-in-combat", "Search"]), G("Search [Action]"),
  chg="2014 Search uses Wisdom (Perception) or Intelligence (Investigation). 2024 Search is a Wisdom check (Insight, Medicine, Perception or Survival); "
      "Investigation moved to the new Study action.",
  kw="perception find look", rel=["study", "hiding"])
T("magic", "Magic (Cast a Spell)", "act", "Cast a spell with a casting time of an action; in 2024 also use a magic item or magical feature.",
  ("B", ["actions-in-combat", "Cast a Spell"]), G("Magic [Action]"),
  chg="2014 calls it Cast a Spell. 2024 renames it Magic and widens it: casting a spell, using a magic item, or using a magical feature that takes an action. "
      "If you cast a spell with a casting time of 1 minute or longer, you take this action on each turn and must keep Concentration.",
  kw="cast a spell magic item activate", rel=["casting-time", "components", "concentration"])
T("utilize", "Utilize (Use an Object)", "act", "Use an object that needs your action, beyond the one free object interaction you get each turn.",
  ("B", ["actions-in-combat", "Use an Object"]), G("Utilize [Action]"),
  chg="2014 calls it Use an Object. 2024 renames it Utilize, for using a nonmagical object; magic items use the Magic action.",
  kw="use an object item potion lever", rel=["your-turn", "magic"])
T("influence", "Influence", "act", "Use a social check to change a creature's attitude (2024).",
  "The 2014 rules have no Influence action. Talking someone round is a Charisma check, called for by the GM; see Social Interaction in the 2014 rules.",
  G("Influence [Action]"), chg="New in 2024.", kw="persuade deceive intimidate persuasion social attitude")
T("study", "Study", "act", "Recall or work out information with an Intelligence check (2024).",
  "The 2014 rules have no Study action. Intelligence (Investigation) checks use the Search action; recalling lore is an Intelligence check the GM calls for.",
  G("Study [Action]"), chg="New in 2024. It takes Investigation and the knowledge skills (Arcana, History, Nature, Religion) out of Search.",
  kw="investigation arcana history nature religion recall", rel=["search"])

# ---- combat
T("your-turn", "Your turn", "combat", "Move up to your Speed and take one action. One free object interaction; a bonus action only if something gives you one.",
  [("B", ["the-order-of-combat", "Your Turn"], {"stop": ["Bonus Actions"]}),
   ("B", ["the-order-of-combat", "Your Turn", "Other Activity on Your Turn"], {"label": "Other Activity on Your Turn"})],
  ("P", ["The Order of Combat", "Your Turn"]), kw="turn movement free interaction communicate", rel=["actions", "bonus-actions", "reactions"])
T("bonus-actions", "Bonus actions", "combat", "Only when a feature, spell or rule gives you one; at most one per turn.",
  ("B", ["the-order-of-combat", "Bonus Actions"]), [("P", ["Actions", "Bonus Actions"]), G("Bonus Action", label="Rules Glossary")],
  kw="bonus action", rel=["casting-time", "two-weapon"])
T("reactions", "Reactions", "combat", "An instant response to a trigger. One per round; it comes back at the start of your turn.",
  ("B", ["the-order-of-combat", "Reactions"]), [("P", ["Actions", "Reactions"]), G("Reaction", label="Rules Glossary")],
  kw="reaction", rel=["opportunity-attacks", "ready"])
T("opportunity-attacks", "Opportunity attacks", "combat", "When a creature you can see leaves your reach, you can use your reaction to make one melee attack against it.",
  ("B", ["making-an-attack", "Opportunity Attacks"]), [("P", ["Melee Attacks", "Opportunity Attacks"]), G("Opportunity Attacks", label="Rules Glossary")],
  chg="Same trigger and the same ways to avoid it (Disengage, teleporting, being moved without using your own movement). "
      "2024 says you can make the attack with a weapon or an Unarmed Strike, and any creature you can see can provoke one (2014 says a hostile creature).",
  kw="aoo provoke leave reach", rel=["disengage", "reactions"])
T("two-weapon", "Two-weapon fighting (Light weapons)", "combat", "Attack with a Light weapon, then make an extra attack with a different Light weapon as a bonus action, without your ability modifier to damage.",
  ("B", ["making-an-attack", "Two-Weapon Fighting"]),
  [("E2", "Light"), ("E2", "Nick")],
  chg="2014 needs a Light melee weapon in each hand. 2024 moves the rule into the Light weapon property: when you take the Attack action and attack with a Light weapon, "
      "you can make one extra attack as a bonus action with a different Light weapon. Thrown Light weapons count. "
      "The Nick weapon mastery lets the extra attack be part of the Attack action, which frees your bonus action.",
  kw="dual wield twf off-hand offhand light nick dagger shortsword", rel=["attack", "bonus-actions"])
T("grapple-shove", "Grapple and shove", "combat", "Grab a creature (it gets the Grappled condition) or push it 5 feet or knock it prone.",
  [("B", ["making-an-attack", "Grappling"], {"label": "Grappling"}), ("B", ["making-an-attack", "Shoving a Creature"], {"label": "Shoving a Creature"})],
  [G("Unarmed Strike", label="Unarmed Strike"), G("Grappling", label="Grappling")],
  chg="2014: a special melee attack that replaces one attack, decided by your Strength (Athletics) check against the target's Athletics or Acrobatics. "
      "2024: grapple and shove are options of the Unarmed Strike. The target makes a Strength or Dexterity saving throw (its choice) against "
      "DC 8 + your Strength modifier + your Proficiency Bonus, and escaping a grapple is a check against that same DC.",
  kw="grab wrestle push shove knock prone unarmed strike athletics", rel=["grappled", "prone", "attack"])
T("cover", "Cover", "combat", "Half cover +2 to AC and Dex saves, three-quarters +5, total cover can't be targeted directly.",
  ("B", ["cover", "Cover"]), ("P", "Cover"), kw="half three-quarters total cover ac", rel=["hiding"])
T("mounted-combat", "Mounted combat", "combat", "Mounting or dismounting costs half your Speed. A controlled mount can only Dash, Disengage or Dodge.",
  ("B", ["mounted-combat", "Mounted Combat"]), ("P", "Mounted Combat"),
  kw="mount horse ride riding dismount", rel=["prone"])

# ---- damage and healing
T("damage-modifiers", "Resistance, vulnerability and immunity", "dmg", "Resistance halves the damage, vulnerability doubles it, immunity ignores it. Several instances count once; other modifiers apply first.",
  ("B", ["damage-and-healing", "Damage Resistance and Vulnerability"]),
  [("P", ["Damage and Healing", "Resistance and Vulnerability"]), ("P", ["Damage and Healing", "Immunity"], {"label": "Immunity"})],
  chg="The rule is the same: multiple resistances (or vulnerabilities) to the same damage count only once, and resistance then vulnerability apply after every other modifier. "
      "2024 spells the order out step by step (other modifiers first, then resistance, then vulnerability) and gives immunity its own rule.",
  kw="resist resistant halve half double immune damage order stacking", rel=["temp-hp"])
T("death-saves", "Dropping to 0 HP and death saves", "dmg", "At 0 HP you fall unconscious and roll a d20 each turn: 10+ succeeds. Three successes stabilize, three failures kill.",
  ("B", ["damage-and-healing", "Dropping to 0 Hit Points"]),
  ("P", ["Damage and Healing", "Dropping to 0 Hit Points"]),
  chg="The death saving throw itself is unchanged (a 20 brings you back with 1 HP, a 1 counts as two failures, damage at 0 HP is a failure, a critical hit two). "
      "Stabilizing is still a DC 10 Wisdom (Medicine) check; in 2024 you make it with the Help action. 2024 also lists the ways to die instantly in one place: massive damage, a Hit Point maximum of 0, and monsters dying at 0 HP.",
  kw="dying death saving throw stabilize stable 0 hp zero instant death massive damage", rel=["unconscious", "help", "knock-out"])
T("knock-out", "Knocking a creature out", "dmg", "When a melee attack would drop a creature to 0 HP, you can leave it unconscious instead.",
  ("B", ["damage-and-healing", "Knocking a Creature Out"]), G("Knocking Out a Creature"),
  chg="2014: the creature falls unconscious and is stable. 2024: it is left at 1 HP, Unconscious, and starts a short rest; it wakes when it regains HP "
      "or someone succeeds on a DC 10 Wisdom (Medicine) check to give first aid.",
  kw="nonlethal non-lethal subdue knock out", rel=["unconscious", "death-saves"])
T("temp-hp", "Temporary hit points", "dmg", "A buffer lost before real HP. They don't stack: keep the higher amount. They aren't healing.",
  ("B", ["damage-and-healing", "Temporary Hit Points"]), ("P", ["Damage and Healing", "Temporary Hit Points"]),
  kw="temp thp buffer stack false life", rel=["damage-modifiers"])
T("resting", "Short and long rests", "dmg", "Short rest: 1 hour, spend Hit Dice. Long rest: 8 hours, regain all HP, and Hit Dice back.",
  [("B", ["resting", "Resting"], {"stop": ["Short Rest"]}), ("B", ["resting", "Short Rest"], {"label": "Short Rest"}), ("B", ["resting", "Long Rest"], {"label": "Long Rest"})],
  [G("Short Rest", label="Short Rest"), G("Long Rest", label="Long Rest")],
  chg="2014 long rest gives back only half your total Hit Dice; 2024 gives back all of them. "
      "2024 also lists what interrupts a rest (rolling Initiative, casting a spell other than a cantrip, taking damage, and for a long rest 1 hour of exertion), "
      "gives short-rest benefits if a long rest stopped after at least 1 hour, and a short rest now also needs at least 1 HP to start (2014 asks that only for a long rest). A long rest removes one Exhaustion level in both (2014 also needs food and drink).",
  kw="rest short long hit dice sleep recover", rel=["exhaustion", "knock-out"])

# ---- spellcasting
T("concentration", "Concentration", "spell", "One concentration effect at a time. Taking damage: Con save, DC 10 or half the damage, whichever is higher.",
  ("B", ["casting-a-spell", "Concentration"]), G("Concentration"),
  chg="Same rule, with three details in 2024: the save DC is capped at 30, you lose Concentration the moment you start casting another Concentration spell, "
      "and it applies to any effect marked Concentration, not just spells. Being Incapacitated still ends it.",
  kw="concentrate con save constitution saving throw break", rel=["incapacitated", "magic"])
T("casting-time", "Casting time and the bonus action spell rule", "spell", "2014: after a bonus action spell, only an action cantrip that turn. 2024: only one spell slot per turn.",
  [("B", ["casting-a-spell", "Casting Time"], {"stop": ["Bonus Action"]}), ("B", ["casting-a-spell", "Casting Time", "Bonus Action"], {"label": "Bonus Action"}),
   ("B", ["casting-a-spell", "Casting Time", "Reactions"], {"label": "Reactions"}), ("B", ["casting-a-spell", "Casting Time", "Longer Casting Times"], {"label": "Longer Casting Times"})],
  [("S", "Casting Time", {"stop": ["One Spell with a Spell Slot per Turn"]}),
   ("S", ["Casting Time", "One Spell with a Spell Slot per Turn"], {"label": "One Spell with a Spell Slot per Turn"}),
   ("S", ["Casting Time", "Reaction and Bonus Action Triggers"], {"label": "Reaction and Bonus Action Triggers"}),
   ("S", ["Casting Time", "Longer Casting Times"], {"label": "Longer Casting Times"})],
  chg="2014: if you cast a spell as a bonus action, the only other spell you can cast that turn is a cantrip with a casting time of one action. "
      "2024 replaces that with a simpler limit: you can expend only one spell slot to cast a spell on each turn. "
      "So a bonus action spell plus a cantrip (any casting time) is fine, and two levelled spells in one turn need one of them to be cast without a slot.",
  kw="bonus action spell two spells one slot per turn quickened cantrip", rel=["magic", "bonus-actions", "components"])
T("components", "Spell components", "spell", "Verbal: speak. Somatic: a free hand to gesture. Material: the item, or a component pouch or focus unless it has a cost or is consumed.",
  ("B", ["casting-a-spell", "Components"]), ("S", "Components"),
  kw="verbal somatic material v s m focus component pouch free hand silence gagged", rel=["casting-time", "hiding"])

# ---- exploration and hazards
T("vision-light", "Vision and light", "explore", "Bright, dim and darkness; lightly and heavily obscured. Darkvision sees dim light as bright and darkness as dim.",
  [("B", ["the-environment", "Vision and Light"])], ("P", ["Exploration", "Vision and Light"]),
  kw="darkvision blindsight truesight tremorsense dim bright darkness obscured fog light", rel=["hiding", "blinded"])
T("hiding", "Hiding and unseen attackers", "explore", "Hide with a Stealth check where you can't be seen. Attacking a target you can't see has disadvantage; attacking one that can't see you has advantage.",
  [("B", ["using-each-ability", "Dexterity", "Hiding"], {"label": "Hiding"}), ("B", ["actions-in-combat", "Hide"], {"label": "Hide action"}),
   ("B", ["making-an-attack", "Unseen Attackers and Targets"], {"label": "Unseen Attackers and Targets"})],
  [("P", ["Exploration", "Hiding"], {"label": "Hiding"}), G("Hide [Action]", label="Hide action"), ("P2", "Unseen Attackers and Targets")],
  chg="2014 hiding is a Dexterity (Stealth) check contested by Perception, and the GM decides when you can hide. "
      "2024 makes it a Hide action with a fixed DC 15 Stealth check while you are Heavily Obscured or behind three-quarters or total cover and out of enemies' sight. "
      "Success gives you the Invisible condition, and your check total becomes the DC to find you.",
  kw="hide stealth sneak hidden invisible unseen attacker perception", rel=["invisible", "cover", "vision-light", "search"])
T("travel-pace", "Travel pace", "explore", "Fast 4 mph (30 miles a day), Normal 3 mph (24), Slow 2 mph (18). Travel past 8 hours risks exhaustion.",
  [("B", ["movement", "Travel Pace"], {"stop": ["Difficult Terrain"]})],
  [("P", ["Exploration", "Travel Pace"]), ("T", "Travel Pace", {"label": "Travel Pace (Gameplay Toolbox)", "stop": ["Vehicles"]})],
  chg="The speeds are the same. The effects changed: 2014 Fast gives -5 to passive Perception and Slow lets you use Stealth. "
      "2024 Fast gives disadvantage on Perception, Survival and Stealth checks, Normal gives disadvantage on Stealth, and Slow gives advantage on Perception and Survival. "
      "Forced march (2014) is called extended travel in 2024; it works the same way.",
  kw="travel overland pace miles forced march extended travel journey", rel=["exhaustion"])
T("falling", "Falling", "explore", "1d6 bludgeoning per 10 feet fallen, up to 20d6; you land prone unless you take no damage.",
  ("B", ["the-environment", "Falling"]), G("Falling [Hazard]"),
  chg="2024 adds falling into water or another liquid: use your reaction for a DC 15 Strength (Athletics) or Dexterity (Acrobatics) check to halve the damage.",
  kw="fall falling damage height", rel=["prone"])
T("suffocating", "Suffocating", "explore", "Hold your breath for 1 + Con modifier minutes (at least 30 seconds); after that, it gets dangerous fast.",
  ("B", ["the-environment", "Suffocating"]), G("Suffocation [Hazard]"),
  chg="2014: once out of breath you survive a number of rounds equal to your Constitution modifier (at least 1), then drop to 0 HP and are dying. "
      "2024: you gain 1 Exhaustion level at the end of each of your turns instead, and lose those levels as soon as you can breathe again.",
  kw="drowning breath underwater choking air suffocation", rel=["exhaustion"])

# ---------------------------------------------------------------- special parts that need a narrower cut
def light_property(name):
    """the 2024 Light property / Nick mastery paragraphs from equipment.md (bold-labelled paragraphs, not headings)."""
    for ln in MD["E"].splitlines():
        if ln.startswith(f"**{name}.**"):
            label = "Light (weapon property)" if name == "Light" else "Nick (weapon mastery)"
            return render([ln[len(f'**{name}.**'):].strip()], label, None)
    raise KeyError(name)

def unseen_2024():
    for i, ln in enumerate(MD["P"].splitlines()):
        if ln.strip() == "> **Unseen Attackers and Targets**":
            buf = []
            for ln2 in MD["P"].splitlines()[i + 1:]:
                if not ln2.startswith(">"): break
                buf.append(re.sub(r"^>\s?", "", ln2))
            return render(buf, "Unseen Attackers and Targets", None)
    raise KeyError("unseen")

_part = part
def part(spec):  # noqa: F811 -- route the two special cases
    if spec[0] == "E2": return light_property(spec[1])
    if spec[0] == "P2": return unseen_2024()
    return _part(spec)

# element ids used on index.html; a topic id (its #anchor) must not reuse one
PAGE_IDS = set(re.findall(r'id="([^"]+)"', (ROOT / "site" / "index.html").read_text(encoding="utf-8")))

def main():
    out, ids = [], set()
    for t in TOPICS:
        assert t["id"] not in ids, t["id"]; ids.add(t["id"])
        assert t["id"] not in PAGE_IDS, f"{t['id']}: clashes with an element id on index.html"
        row = dict(t)
        row["e14"] = ed(t["e14"], t["id"]); row["e24"] = ed(t["e24"], t["id"])
        for k in ("e14", "e24"):
            if "html" in row[k] and len(re.sub(r"<[^>]+>", "", row[k]["html"])) < 40:
                sys.exit(f"{t['id']} {k}: text too short, check the source path")
        out.append(row)
    for t in out:
        for r in t["rel"]:
            if r not in ids: sys.exit(f"{t['id']}: unknown related topic {r}")
    data = {"topics": out}
    js = "/* generated by tools/build_data.py from source/ -- do not edit by hand */\nwindow.RULES = " + \
         json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    OUT.write_text(js, encoding="utf-8")
    print(f"rules.js: {len(out)} topics, {len(js) // 1024} KB")

if __name__ == "__main__":
    main()
