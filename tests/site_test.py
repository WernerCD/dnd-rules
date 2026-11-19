"""Rules Reference checks, run by tools/smoke_test.py after the shared tests:  def run(page, base, check)."""


def run(page, base, check):
    def fresh(url=""):
        page.goto(base + url, wait_until="load")
        page.wait_for_timeout(500)

    # every topic in the data renders as a card, with a unique id
    fresh()
    n_data = page.evaluate("window.RULES.topics.length")
    n_cards = page.locator("#list .topic").count()
    check(n_data >= 48, f"[rules] data has all topics ({n_data})")
    check(n_cards == n_data, f"[rules] every topic renders a card ({n_cards} of {n_data})")
    ids = page.evaluate("[...document.querySelectorAll('[id]')].map(e => e.id)")
    check(len(ids) == len(set(ids)), "[rules] no duplicate element ids (a topic anchor clashing with a control)")

    # search narrows the list and finds rules by their text
    page.fill("#q", "bonus action spell")
    page.wait_for_timeout(400)
    titles = page.locator("#list .topic .t-title").all_inner_texts()
    check(0 < len(titles) < n_cards, f"[rules] search narrows the list ({len(titles)} shown)")
    check(any("Casting time" in t for t in titles), "[rules] search 'bonus action spell' finds Casting time")
    page.fill("#q", "zzzz-no-such-rule")
    page.wait_for_timeout(400)
    check(page.locator("#empty").is_visible(), "[rules] a search with no matches says so")
    page.fill("#q", "")

    # category chip filters to conditions only
    page.click("#cats [data-cat='cond']")
    page.wait_for_timeout(200)
    cats = page.eval_on_selector_all("#list .topic", "els => [...new Set(els.map(e => e.dataset.cat))]")
    check(cats == ["cond"] and page.locator("#list .topic").count() == 15, f"[rules] Conditions chip shows the 15 conditions ({cats})")

    # #condition-<name> (the Character Sheet's links) and #<id> open the topic and scroll to it
    for h, tid in (("#condition-poisoned", "poisoned"), ("#condition-Stunned", "stunned"), ("#grapple-shove", "grapple-shove")):
        fresh(h)
        page.wait_for_timeout(600)
        is_open = page.evaluate(f"document.getElementById('{tid}').classList.contains('open')")
        top = page.evaluate(f"document.getElementById('{tid}').getBoundingClientRect().top")
        check(is_open, f"[rules] {h} opens {tid}")
        check(0 <= top < 300, f"[rules] {h} scrolls {tid} into view below the filter bar (top {top:.0f}px)")

    # a condition named in the text links to that condition's card
    fresh("#grapple-shove")
    page.click("#grapple-shove a.xref[href='#grappled']")
    page.wait_for_timeout(900)
    check(page.evaluate("document.getElementById('grappled').classList.contains('open')"), "[rules] in-text condition link opens Grappled")

    # edition switch changes the text; Compare editions shows both
    fresh("?ed=2014#exhaustion")
    t14 = page.inner_text("#exhaustion .t-body")
    check("Disadvantage on ability checks" in t14, "[rules] 2014 Exhaustion shows the six-level table")
    page.click("[data-ed='2024']")
    page.wait_for_timeout(300)
    if not page.evaluate("document.getElementById('exhaustion').classList.contains('open')"):
        page.locator("#exhaustion .t-tog").click()
    t24 = page.inner_text("#exhaustion .t-body")
    check("reduced by 2 times your Exhaustion level" in t24, "[rules] 2024 Exhaustion shows the -2 per level rule")
    page.check("#compare")
    page.wait_for_timeout(300)
    if not page.evaluate("document.getElementById('exhaustion').classList.contains('open')"):
        page.locator("#exhaustion .t-tog").click()
    both = page.locator("#exhaustion .cmp > section").count()
    tb = page.inner_text("#exhaustion .t-body")
    check(both == 2 and "Disadvantage on ability checks" in tb and "2 times your Exhaustion level" in tb,
          "[rules] Compare editions shows the 2014 and 2024 text side by side")

    # every topic that differs carries a 'what changed' note, and SRD attribution shows
    page.uncheck("#compare")
    page.click("#onlyChg")
    page.wait_for_timeout(300)
    n_chg = page.locator("#list .topic").count()
    check(0 < n_chg < n_cards, f"[rules] 'Changed in 2024' filter narrows the list ({n_chg})")
    page.click("#expandAll")
    page.wait_for_timeout(300)
    check(page.locator("#list .topic .chg").count() == n_chg, "[rules] each changed topic shows its 'What changed in 2024' note")
    check(page.locator("#list .topic .src").first.inner_text().startswith("Source: SRD 5."), "[rules] rules text shows its SRD source")
