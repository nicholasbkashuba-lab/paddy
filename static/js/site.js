/* Paddy Mac's — progressive enhancement only.
   The page is fully readable with this file blocked; everything here
   just makes it current. Data comes from window.PM, injected by build.py. */

(function () {
  'use strict';
  var PM = window.PM || { hours: [], gigs: [] };
  var DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

  /* Eastern time regardless of where the visitor is sitting. Someone
     checking from California should see the pub's clock, not their own. */
  function easternNow() {
    var parts = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      weekday: 'short', hour: 'numeric', minute: 'numeric', hour12: false
    }).formatToParts(new Date());
    function get(t) { return parts.find(function (p) { return p.type === t; }).value; }
    var map = { Sun:0, Mon:1, Tue:2, Wed:3, Thu:4, Fri:5, Sat:6 };
    return { dow: map[get('weekday')], mins: parseInt(get('hour'),10) * 60 + parseInt(get('minute'),10) };
  }

  function fmt(mins) {
    var m = mins % 1440, h = Math.floor(m / 60), mm = m % 60;
    var ap = h >= 12 ? 'pm' : 'am', h12 = h % 12 || 12;
    return h12 + (mm ? ':' + String(mm).padStart(2, '0') : '') + ap;
  }

  function status(now) {
    var yest = (now.dow + 6) % 7, y = PM.hours[yest];
    /* still going from last night — a 2am close belongs to yesterday */
    var carry = y && y.close && y.close > 1440 && now.mins < (y.close - 1440);
    var t = PM.hours[now.dow];
    if (carry) return { open: true, until: y.close };
    if (t && t.open !== null && now.mins >= t.open && now.mins < t.close) {
      return { open: true, until: t.close };
    }
    for (var i = 0; i < 8; i++) {
      var d = (now.dow + i) % 7, h = PM.hours[d];
      if (!h || h.open === null) continue;
      if (i === 0 && now.mins >= h.open) continue;
      return {
        open: false,
        when: i === 0 ? 'today' : i === 1 ? 'tomorrow' : DAYS[d],
        at: h.open
      };
    }
    return { open: false };
  }

  function paint() {
    var now = easternNow(), s = status(now);
    var dot = document.getElementById('nowDot');
    var state = document.getElementById('nowState');
    var detail = document.getElementById('nowDetail');
    if (!dot) return;

    dot.classList.toggle('is-shut', !s.open);

    if (s.open) {
      state.textContent = 'Open now';
      detail.innerHTML = 'Last call around <b>' + fmt(s.until) + '</b>';
    } else {
      state.textContent = 'Closed';
      detail.innerHTML = s.at !== undefined
        ? 'Back ' + s.when + ' at <b>' + fmt(s.at) + '</b>'
        : 'See the hours below';
    }

    var tonight = PM.gigs.filter(function (g) { return g.dow === now.dow; })[0];
    if (tonight) detail.innerHTML += ' &nbsp;·&nbsp; Live music from <b>8pm</b>';

    /* relabel tonight's gig row and today's hours row */
    Array.prototype.forEach.call(document.querySelectorAll('.gig'), function (el) {
      var is = Number(el.dataset.dow) === now.dow;
      el.classList.toggle('is-tonight', is);
      if (is) el.querySelector('.gig__day').textContent = 'Tonight';
    });
    Array.prototype.forEach.call(document.querySelectorAll('.hours li'), function (el) {
      el.classList.toggle('is-today', Number(el.dataset.dow) === now.dow);
    });
  }

  /* nav */
  var toggle = document.getElementById('navToggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = document.getElementById('navLinks').classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? 'Close' : 'Menu';
    });
  }

  /* reveal on scroll */
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var targets = document.querySelectorAll('.rv');
  if (reduced || !('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(targets, function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    Array.prototype.forEach.call(targets, function (el) { io.observe(el); });
  }

  paint();
  setInterval(paint, 60000);
})();
