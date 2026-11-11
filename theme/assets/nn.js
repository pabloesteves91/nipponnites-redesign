/* Nippon Nites – Skizzenbuch-Motion. Keine Bibliothek. */
(function () {
  var doc = document.documentElement;
  var ruhig = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 1–4: Linien zeichnen, Marker, Polaroids fallen, Checkliste – alles beim Sichtbarwerden
  var ziele = document.querySelectorAll('[data-zeichnen], .nn-marker, .nn-foto[data-fallen], [data-abhaken]');
  if (ruhig || !('IntersectionObserver' in window)) {
    ziele.forEach(function (el) { el.classList.add('is-da'); });
  } else {
    var io = new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        if (el.hasAttribute('data-abhaken')) {
          // Kästchen nacheinander abhaken
          el.querySelectorAll('[data-zeichnen]').forEach(function (h, i) {
            setTimeout(function () { h.classList.add('is-da'); }, 220 * i);
          });
        } else {
          el.classList.add('is-da');
        }
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -12% 0px' });
    ziele.forEach(function (el) {
      if (el.closest('[data-abhaken]') && el.hasAttribute('data-zeichnen')) return;
      io.observe(el);
    });
  }

  // 5: Scroll-Story – setzt --p (0–1) und blendet die Ebenen ineinander
  document.querySelectorAll('[data-prozess]').forEach(function (box) {
    var ebenen = box.querySelectorAll('.nn-prozess__ebene');
    var schritte = box.querySelectorAll('.nn-prozess__schritte li');
    var wisch = box.querySelector('.nn-prozess__wisch');
    var n = ebenen.length;
    var statisch = ruhig || matchMedia('(max-width: 860px)').matches;
    function setze(p) {
      var pos = p * (n - 1); // 0 … n-1
      var aktiv = Math.min(n - 1, Math.round(pos));
      ebenen.forEach(function (eb, i) {
        if (i === 0) return;
        var z = Math.max(0, Math.min(1, pos - (i - 1)));
        eb.style.setProperty('--zeig', z.toFixed(3));
      });
      var teil = pos - Math.floor(pos);
      if (wisch) {
        wisch.style.setProperty('--wisch', teil.toFixed(3));
        wisch.style.setProperty('--wisch-sicht', teil > .02 && teil < .98 && pos < n - 1 ? 1 : 0);
      }
      schritte.forEach(function (s, i) { s.classList.toggle('is-aktiv', i === aktiv); });
    }
    if (statisch) {
      // Handy / ruhig: Schritte antippbar, Bild wechselt ohne Scroll-Bindung
      setze(0);
      schritte.forEach(function (s, i) {
        s.addEventListener('click', function () { setze(n > 1 ? i / (n - 1) : 0); });
      });
      return;
    }
    var tick = false;
    function rechne() {
      tick = false;
      var r = box.getBoundingClientRect();
      var weg = r.height - innerHeight;
      setze(Math.max(0, Math.min(1, -r.top / (weg || 1))));
    }
    addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(rechne); } }, { passive: true });
    addEventListener('resize', rechne);
    rechne();
  });

  // Mengenfeld +/- auf der Produktseite
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-menge]');
    if (!b) return;
    var input = b.parentNode.querySelector('input');
    input.value = Math.max(1, (parseInt(input.value, 10) || 1) + parseInt(b.getAttribute('data-menge'), 10));
  });

  doc.classList.add('nn-bereit');
})();
