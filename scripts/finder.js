(function () {
  var q = document.getElementById('q'), sugg = document.getElementById('sugg'), picked = document.getElementById('picked'),
      all = document.getElementById('all'), out = document.getElementById('results'), area = document.getElementById('area');
  if (!q) return;
  var data = null, chosen = [], active = -1;
  function norm(s) { return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]/g, ''); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  fetch('/assets/search.json').then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    var pre = new URLSearchParams(location.search).get('brands');
    if (pre) pre.split(',').forEach(function (sl) { d.b.forEach(function (b, i) { if (b[1] === sl && chosen.indexOf(i) < 0) chosen.push(i); }); });
    render();
  });
  function matches(text) {
    var t = norm(text); if (!t || !data) return [];
    return data.b.map(function (b, i) { return [b, i]; })
      .filter(function (x) { return chosen.indexOf(x[1]) < 0 && norm(x[0][0]).indexOf(t) >= 0; })
      .sort(function (a, b) { return norm(a[0][0]).indexOf(t) - norm(b[0][0]).indexOf(t); }).slice(0, 8);
  }
  function showSugg() {
    var m = matches(q.value); active = m.length ? 0 : -1;
    if (!m.length) { sugg.hidden = true; sugg.innerHTML = ''; return; }
    sugg.innerHTML = m.map(function (x, k) { return '<li role="option" data-i="' + x[1] + '" aria-selected="' + (k === 0) + '">' + esc(x[0][0]) + '</li>'; }).join('');
    sugg.hidden = false;
  }
  function add(i) { if (chosen.indexOf(i) < 0) chosen.push(i); q.value = ''; sugg.hidden = true; render(); q.focus(); }
  q.addEventListener('input', showSugg);
  q.addEventListener('keydown', function (e) {
    var items = sugg.querySelectorAll('li');
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      if (!items.length) return; e.preventDefault();
      active = (active + (e.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length;
      items.forEach(function (li, k) { li.setAttribute('aria-selected', k === active); });
    } else if (e.key === 'Enter') {
      e.preventDefault(); if (items[active]) add(+items[active].dataset.i);
    } else if (e.key === 'Backspace' && !q.value && chosen.length) { chosen.pop(); render(); }
  });
  sugg.addEventListener('mousedown', function (e) { var li = e.target.closest('li'); if (li) { e.preventDefault(); add(+li.dataset.i); } });
  q.addEventListener('blur', function () { setTimeout(function () { sugg.hidden = true; }, 150); });
  picked.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return; chosen.splice(chosen.indexOf(+b.dataset.i), 1); render();
  });
  all.addEventListener('change', render);
  if (area) area.addEventListener('change', render);
  var me = null, nearmsg = '';
  function miles(a, c, d, e) { var r = Math.PI / 180, x = (d - a) * r, y = (e - c) * r, h = Math.sin(x / 2) * Math.sin(x / 2) + Math.cos(a * r) * Math.cos(d * r) * Math.sin(y / 2) * Math.sin(y / 2); return 3958.8 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h)); }
  function render() {
    if (!data) return;
    picked.innerHTML = chosen.map(function (i) { return '<span class="pick">' + esc(data.b[i][0]) + '<button type="button" data-i="' + i + '" aria-label="Remove ' + esc(data.b[i][0]) + '">×</button></span>'; }).join('');
    var url = chosen.length ? '?brands=' + chosen.map(function (i) { return data.b[i][1]; }).join(',') : location.pathname;
    history.replaceState(null, '', url);
    if (!chosen.length) { out.innerHTML = ''; return; }
    var need = all.checked ? chosen.length : 1;
    var boro = area ? area.value : '', metro = boro.indexOf('m:') === 0 ? boro.slice(2) : '';
    var label = metro ? (metro === 'Los Angeles' ? 'the Los Angeles area' : metro) : (boro ? (boro === 'Los Angeles' ? 'the City of Los Angeles' : boro) : (data.m || ['New York City']).join(' and '));
    var res = data.s.filter(function (s) { return !boro || (metro ? s[10] === metro : s[7] === boro); }).map(function (s) {
      var hit = chosen.filter(function (i) { return s[5].indexOf(i) >= 0; });
      return { s: s, hit: hit };
    }).filter(function (r) { return r.hit.length >= need; })
      .map(function (r) { r.d = (me && r.s[8] != null) ? miles(me[0], me[1], r.s[8], r.s[9]) : null; return r; })
      .sort(function (a, b) { return b.hit.length - a.hit.length || (me ? ((a.d === null) - (b.d === null) || a.d - b.d) : 0) || (data.m ? data.m.indexOf(a.s[10]) - data.m.indexOf(b.s[10]) : 0) || (a.s[2] !== 'Brand store') - (b.s[2] !== 'Brand store') || a.s[3].localeCompare(b.s[3]) || a.s[0].localeCompare(b.s[0]); });
    var names = chosen.map(function (i) { return data.b[i][0]; });
    var head = res.length + ' store' + (res.length === 1 ? '' : 's') + ' in ' + label + ' carry ' +
      (chosen.length === 1 ? esc(names[0]) : (all.checked ? 'all of: ' : 'at least one of: ') + names.map(esc).join(', '));
    var links = chosen.map(function (i) { return '<a href="/brands/' + data.b[i][1] + '/">' + esc(data.b[i][0]) + ' page</a>'; }).join(' · ');
    if (!res.length) {
      out.innerHTML = '<h2>' + head + '</h2><div class="empty"><p>No store we\'ve checked carries ' + (all.checked && chosen.length > 1 ? 'all of these brands. Try unticking "Only show stores that carry all of these brands."' : 'this brand yet.') + '</p></div>';
      return;
    }
    var cards = res.slice(0, 60).map(function (r) {
      var s = r.s, badges = r.hit.map(function (i) { return '<span class="badge ok">' + esc(data.b[i][0]) + '</span>'; }).join('') +
        (r.hit.some(function (i) { return s[6].indexOf(i) >= 0; }) ? '<span class="badge warn">Selection varies</span>' : '');
      var maps = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(s[0] + ', ' + s[4]);
      return '<article class="card store"><div class="cardhead"><a class="cardtitle" href="/stores/' + s[1] + '/">' + esc(s[0]) + '</a></div>' +
        '<p class="meta">' + esc(s[2]) + ' · ' + esc(s[3]) + '<br>' + esc(s[4]) + '</p>' + (me ? '<p class="dist">' + (r.d === null ? 'Distance not available' : (r.d < 0.1 ? 'Under 0.1' : r.d.toFixed(1)) + ' mi away (straight line)') + '</p>' : '') + '<div class="badges">' + badges + '</div>' +
        '<div class="btns"><a class="btn primary" href="' + maps + '" target="_blank" rel="noopener">Directions</a><a class="btn" href="/stores/' + s[1] + '/">Store details</a></div></article>';
    }).join('');
    out.innerHTML = '<h2>' + head + '</h2><p class="sub">' + links + (res.length > 60 ? ' · showing the first 60' : '') + '</p>' +
      '<div class="nearbar"><button type="button" class="nearbtn" id="fnear"' + (me ? ' disabled>Nearest first' : '>Show nearest to me first') + '</button><span class="nearmsg" role="status">' + (nearmsg || '') + '</span></div><div class="cards">' + cards + '</div>';
    var nb = document.getElementById('fnear');
    if (nb && !me) nb.addEventListener('click', function () {
      if (!navigator.geolocation) { nearmsg = 'Your browser is not able to share your location.'; render(); return; }
      nearmsg = 'Finding your location…'; render();
      navigator.geolocation.getCurrentPosition(function (p) { me = [p.coords.latitude, p.coords.longitude]; nearmsg = 'Sorted by distance from you. Your location stays on your device.'; render(); },
        function () { nearmsg = 'Location not shared, so stores stay in the usual order.'; render(); }, { timeout: 10000, maximumAge: 300000 });
    });
  }
})();
