/* D&D Rules Reference: search, category chips, edition switch and topic cards over window.RULES (built by tools/build_data.py). */
(function () {
  'use strict';
  var REPO = 'dnd-rules';
  var KEY = 'dr.edition';            // { ed: '2014'|'2024', manual: bool }
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode */ } }
  };
  var CATS = [
    ['all', 'All'], ['cond', 'Conditions'], ['act', 'Actions'], ['combat', 'Combat'],
    ['dmg', 'Damage & healing'], ['spell', 'Spellcasting'], ['explore', 'Exploration']
  ];
  var CAT_NAME = {}; CATS.forEach(function (c) { CAT_NAME[c[0]] = c[1]; });
  var CAT_ONE = { cond: 'Condition', act: 'Action', combat: 'Combat', dmg: 'Damage & healing', spell: 'Spellcasting', explore: 'Exploration' };
  var ED_SRC = { '2014': 'SRD 5.1', '2024': 'SRD 5.2.1' };

  var TOPICS = (window.RULES && window.RULES.topics) || [];
  var BY_ID = {};
  function plain(h) { return (h || '').replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/\s+/g, ' ').trim(); }
  TOPICS.forEach(function (t) {
    BY_ID[t.id] = t;
    t.t14 = plain(t.e14.html || t.e14.none); t.t24 = plain(t.e24.html || t.e24.none);
    t.head = (t.title + ' ' + t.kw + ' ' + CAT_ONE[t.cat]).toLowerCase();
    t.sumL = t.sum.toLowerCase();
  });

  /* ---------------- state */
  var saved = store.get(KEY, null);
  var params = new URLSearchParams(location.search);
  var state = {
    ed: params.get('ed') === '2014' || params.get('ed') === '2024' ? params.get('ed') : (saved && saved.ed) || '2024',
    manual: !!(saved && saved.manual) || !!params.get('ed'),
    cat: CAT_NAME[params.get('cat')] ? params.get('cat') : 'all',
    q: params.get('q') || '',
    onlyChg: params.get('chg') === '1',
    compare: params.get('cmp') === '1',
    open: {}
  };
  function activeCh() { try { return window.DndChar ? DndChar.active() : null; } catch (e) { return null; } }
  var lastChEd = null;
  (function followChar() {
    var ch = activeCh();
    if (ch && (ch.ed === '2014' || ch.ed === '2024')) { lastChEd = ch.ed; if (!state.manual) state.ed = ch.ed; }
  })();

  var $ = function (id) { return document.getElementById(id); };
  var list = $('list'), toc = $('toc'), search = $('q');

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function terms() { return state.q.toLowerCase().split(/\s+/).filter(Boolean); }
  function bodyText(t) { return (state.compare ? t.t14 + ' ' + t.t24 : (state.ed === '2014' ? t.t14 : t.t24)).toLowerCase(); }
  function matches(t, ws) {
    if (state.cat !== 'all' && t.cat !== state.cat) return false;
    if (state.onlyChg && !t.chg) return false;
    if (!ws.length) return true;
    var hay = t.head + ' ' + t.sumL + ' ' + (t.chg ? t.chg.toLowerCase() : '') + ' ' + bodyText(t);
    return ws.every(function (w) { return hay.indexOf(w) >= 0; });
  }
  function mark(text, ws) {
    var h = esc(text);
    if (!ws.length) return h;
    var rx = new RegExp('(' + ws.map(function (w) { return esc(w).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }).join('|') + ')', 'gi');
    return h.replace(rx, '<mark>$1</mark>');
  }
  function snippet(t, ws) {
    if (!ws.length) return '';
    var inHead = ws.every(function (w) { return (t.head + ' ' + t.sumL).indexOf(w) >= 0; });
    if (inHead) return '';
    var src = state.compare ? t.t14 + ' … ' + t.t24 : (state.ed === '2014' ? t.t14 : t.t24);
    var low = src.toLowerCase(), at = -1;
    for (var i = 0; i < ws.length && at < 0; i++) at = low.indexOf(ws[i]);
    if (at < 0) return '';
    var a = Math.max(0, at - 60), b = Math.min(src.length, at + 120);
    return '<p class="t-snip">' + (a ? '… ' : '') + mark(src.slice(a, b), ws) + (b < src.length ? ' …' : '') + '</p>';
  }

  function edBlock(t, ed) {
    var e = ed === '2014' ? t.e14 : t.e24;
    if (e.none) {
      return '<div class="ed-none"><p>' + esc(e.none) + '</p>' +
        (state.compare ? '' : '<p><button type="button" class="btn" data-goed="' + (ed === '2014' ? '2024' : '2014') + '" data-id="' + t.id + '">Read the ' + (ed === '2014' ? '2024' : '2014') + ' rule</button></p>') + '</div>';
    }
    return '<div class="srd">' + e.html + '</div><p class="src">Source: ' + ED_SRC[ed] + ' (CC BY 4.0)</p>';
  }
  function body(t) {
    var h = '';
    if (t.chg) h += '<div class="chg"><b>What changed in 2024.</b> ' + t.chg + '</div>';
    if (state.compare) {
      h += '<div class="cmp"><section><h4 class="ed-h">2014 rules</h4>' + edBlock(t, '2014') + '</section>' +
           '<section><h4 class="ed-h">2024 rules</h4>' + edBlock(t, '2024') + '</section></div>';
    } else {
      h += edBlock(t, state.ed);
    }
    if (t.rel.length) {
      h += '<p class="rel">See also: ' + t.rel.map(function (r) { return '<a href="#' + r + '" class="xref">' + esc(BY_ID[r].title) + '</a>'; }).join(', ') + '</p>';
    }
    return h;
  }
  function only(t) {
    if (t.e14.none) return '2024 only';
    if (t.e24.none) return '2014 only';
    return '';
  }
  function card(t, ws) {
    var open = !!state.open[t.id];
    var o = only(t);
    return '<article class="topic' + (open ? ' open' : '') + '" id="' + t.id + '" data-cat="' + t.cat + '" data-spot>' +
      '<div class="t-head" data-tog="' + t.id + '">' +
        '<h3 class="t-title"><a href="#' + t.id + '" data-tog="' + t.id + '">' + mark(t.title, ws) + '</a></h3>' +
        '<div class="t-tags"><span class="tag cat-' + t.cat + '">' + esc(CAT_ONE[t.cat]) + '</span>' +
          (t.chg && !o ? '<span class="tag tag-chg">Changed in 2024</span>' : '') +
          (o ? '<span class="tag tag-chg">' + o + '</span>' : '') + '</div>' +
        '<button type="button" class="t-copy" data-copy="' + t.id + '" aria-label="Copy a link to ' + esc(t.title) + '" title="Copy link">#</button>' +
      '</div>' +
      '<p class="t-sum">' + mark(t.sum, ws) + '</p>' + snippet(t, ws) +
      '<button type="button" class="t-tog" data-tog="' + t.id + '" aria-expanded="' + open + '" aria-controls="b-' + t.id + '">' + (open ? 'Hide rules' : 'Show rules') + '</button>' +
      '<div class="t-body" id="b-' + t.id + '"' + (open ? '' : ' hidden') + '>' + (open ? body(t) : '') + '</div>' +
    '</article>';
  }

  /* ---------------- render */
  var shown = [];
  function render(keepFocus) {
    var ws = terms();
    shown = TOPICS.filter(function (t) { return matches(t, ws); });
    list.innerHTML = shown.map(function (t) { return card(t, ws); }).join('');
    $('empty').hidden = shown.length > 0;
    $('count').textContent = shown.length === TOPICS.length ? 'All ' + TOPICS.length + ' topics' : shown.length + ' of ' + TOPICS.length + ' topics';
    var ch = activeCh();
    $('edNote').textContent = (state.compare ? 'Showing 2014 and 2024 side by side.' : 'Showing the ' + state.ed + ' rules (' + ED_SRC[state.ed] + ').') +
      (ch && ch.ed && !state.manual ? ' Following ' + ch.name + '.' : '');
    renderToc();
    paintControls();
    writeUrl();
    if (keepFocus && keepFocus.focus) keepFocus.focus();
  }
  function renderToc() {
    var groups = {};
    shown.forEach(function (t) { (groups[t.cat] = groups[t.cat] || []).push(t); });
    var h = '';
    CATS.slice(1).forEach(function (c) {
      var g = groups[c[0]]; if (!g) return;
      h += '<h3>' + esc(c[1]) + '</h3><ul>' + g.map(function (t) { return '<li><a href="#' + t.id + '">' + esc(t.title) + (t.chg ? ' <span class="dot" title="Changed in 2024" aria-label="changed in 2024"></span>' : '') + '</a></li>'; }).join('') + '</ul>';
    });
    toc.innerHTML = h;
  }
  function paintControls() {
    document.querySelectorAll('[data-ed]').forEach(function (b) { b.setAttribute('aria-checked', String(b.dataset.ed === state.ed && !state.compare)); });
    var ws = terms();
    $('cats').innerHTML = CATS.map(function (c) {
      var n = TOPICS.filter(function (t) { var save = state.cat; state.cat = c[0]; var ok = matches(t, ws); state.cat = save; return ok; }).length;
      return '<button type="button" class="chip' + (n ? '' : ' zero') + '" data-cat="' + c[0] + '" aria-pressed="' + (state.cat === c[0]) + '">' + esc(c[1]) + ' <span class="n">' + n + '</span></button>';
    }).join('');
    $('onlyChg').checked = state.onlyChg; $('compare').checked = state.compare;
    if (document.activeElement !== search) search.value = state.q;
  }
  function writeUrl() {
    var p = new URLSearchParams();
    if (state.manual) p.set('ed', state.ed);
    if (state.cat !== 'all') p.set('cat', state.cat);
    if (state.q) p.set('q', state.q);
    if (state.onlyChg) p.set('chg', '1');
    if (state.compare) p.set('cmp', '1');
    var s = p.toString();
    try { history.replaceState(null, '', location.pathname + (s ? '?' + s : '') + location.hash); } catch (e) { /* file:// */ }
  }

  /* open or close one topic in place (no full re-render, so focus and scroll stay put) */
  function setOpen(id, open) {
    var t = BY_ID[id], el = $(id); if (!t) return;
    state.open[id] = open;
    if (!el) return;
    var b = el.querySelector('.t-body'), btn = el.querySelector('.t-tog');
    el.classList.toggle('open', open);
    b.innerHTML = open ? body(t) : ''; b.hidden = !open;
    btn.setAttribute('aria-expanded', String(open)); btn.textContent = open ? 'Hide rules' : 'Show rules';
    if (open && window.DndUI && DndUI.enter) { try { DndUI.enter(b); } catch (e) { /* motion is decoration */ } }
  }
  function goTo(id, opts) {
    var t = BY_ID[id]; if (!t) return;
    if (!$(id)) {   // filtered out: clear the filters so the topic shows
      state.cat = 'all'; state.q = ''; state.onlyChg = false; render();
    }
    setOpen(id, true);
    setCtlH();
    var el = $(id);
    if (el) {
      el.scrollIntoView({ block: 'start', behavior: (opts && opts.instant) || (window.DndUI && DndUI.reduced) ? 'auto' : 'smooth' });
      el.classList.add('flash'); setTimeout(function () { el.classList.remove('flash'); }, 1200);
      var a = el.querySelector('.t-title a'); if (a) a.focus({ preventScroll: true });
    }
  }

  /* ---------------- events */
  document.querySelector('.controls').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    if (b.dataset.ed) { state.ed = b.dataset.ed; state.manual = true; state.compare = false; store.set(KEY, { ed: state.ed, manual: true }); render(b); return; }
    if (b.dataset.cat) { state.cat = b.dataset.cat; render(); var nb = document.querySelector('#cats [data-cat="' + state.cat + '"]'); if (nb) nb.focus(); return; }
    if (b.id === 'expandAll') { shown.forEach(function (t) { setOpen(t.id, true); }); return; }
    if (b.id === 'collapseAll') { shown.forEach(function (t) { setOpen(t.id, false); }); return; }
    if (b.id === 'printBtn') { window.print(); }
  });
  var qTimer;
  search.addEventListener('input', function () {
    clearTimeout(qTimer);
    qTimer = setTimeout(function () { state.q = search.value.trim(); render(search); }, 120);
  });
  search.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && search.value) { search.value = ''; state.q = ''; render(search); e.preventDefault(); }
    if (e.key === 'Enter' && shown.length === 1) { goTo(shown[0].id); }
  });
  $('onlyChg').addEventListener('change', function (e) { state.onlyChg = e.target.checked; render(e.target); });
  $('compare').addEventListener('change', function (e) { state.compare = e.target.checked; render(e.target); });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName) && !e.ctrlKey && !e.metaKey) { e.preventDefault(); search.focus(); search.select(); }
  });

  list.addEventListener('click', function (e) {
    var cp = e.target.closest('[data-copy]');
    if (cp) {
      var url = location.origin + location.pathname + (state.manual ? '?ed=' + state.ed : '') + '#' + cp.dataset.copy;
      var done = function () { cp.textContent = '✓'; cp.setAttribute('aria-label', 'Link copied'); if (window.DndUI && DndUI.pop) DndUI.pop(cp); setTimeout(function () { cp.textContent = '#'; cp.setAttribute('aria-label', 'Copy a link to ' + BY_ID[cp.dataset.copy].title); }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { location.hash = cp.dataset.copy; });
      else location.hash = cp.dataset.copy;
      return;
    }
    var ge = e.target.closest('[data-goed]');
    if (ge) { state.ed = ge.dataset.goed; state.manual = true; store.set(KEY, { ed: state.ed, manual: true }); render(); goTo(ge.dataset.id, { instant: true }); return; }
    var x = e.target.closest('a.xref');
    if (x) { e.preventDefault(); var id = x.getAttribute('href').slice(1); try { history.pushState(null, '', '#' + id); } catch (er) { /* */ } goTo(id); return; }
    var tg = e.target.closest('[data-tog]');
    if (tg && !e.target.closest('.t-body')) {
      if (tg.tagName === 'A' && (e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1)) return;   // let it open in a new tab
      e.preventDefault();
      var tid = tg.dataset.tog, now = !state.open[tid];
      setOpen(tid, now);
      if (now) { try { history.replaceState(null, '', location.pathname + location.search + '#' + tid); } catch (er) { /* */ } }
    }
  });
  toc.addEventListener('click', function (e) {
    var a = e.target.closest('a'); if (!a) return;
    e.preventDefault(); var id = a.getAttribute('href').slice(1);
    try { history.pushState(null, '', '#' + id); } catch (er) { /* */ }
    goTo(id);
  });
  window.addEventListener('hashchange', function () { var id = location.hash.slice(1); if (BY_ID[id]) goTo(id); });
  window.addEventListener('popstate', function () { var id = location.hash.slice(1); if (BY_ID[id]) goTo(id, { instant: true }); });

  /* the header picker or another tab changed the character: follow its edition unless the user picked one here */
  if (window.DndChar) DndChar.onChange(function (ch) {
    var ed = ch && (ch.ed === '2014' || ch.ed === '2024') ? ch.ed : null;
    if (ed === lastChEd) { render(); return; }
    lastChEd = ed;
    if (ed && !state.manual && ed !== state.ed) state.ed = ed;
    render();
  });
  /* another tab picked an edition here */
  window.addEventListener('storage', function (e) {
    if (e.key !== KEY) return;
    var v = store.get(KEY, null); if (!v) return;
    if (v.ed !== state.ed || !!v.manual !== state.manual) { state.ed = v.ed; state.manual = !!v.manual; render(); }
  });

  /* the sticky filter bar's height: topics scroll to just below it, and the topic list sticks under it */
  var ctl = document.querySelector('.controls');
  function setCtlH() {
    var sticky = getComputedStyle(ctl).position === 'sticky';
    document.documentElement.style.setProperty('--ctl-h', (sticky ? ctl.offsetHeight : 0) + 'px');
  }
  setCtlH();
  if (window.ResizeObserver) new ResizeObserver(setCtlH).observe(ctl); else window.addEventListener('resize', setCtlH);

  render();
  var h0 = location.hash.slice(1);
  if (BY_ID[h0]) goTo(h0, { instant: true });
})();
