/* Nippon Nites – interactions. No framework, ~10 KB. */
(() => {
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const body = document.body;
  const SHOP = body.dataset.shop || 'https://nipponnites.com';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = (n) => 'CHF ' + Number(n).toFixed(2);

  /* ---------- clock: Winterthur × Tokyo ---------- */
  const clocks = $$('[data-tz]');
  const tick = () => clocks.forEach((el) => {
    const t = new Intl.DateTimeFormat('de-CH', { timeZone: el.dataset.tz, hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date());
    el.textContent = t;
    const h = parseInt(t, 10);
    el.parentElement.classList.toggle('is-night', h >= 22 || h < 5);
  });
  if (clocks.length) { tick(); setInterval(tick, 15000); }

  /* ---------- header hide on scroll ---------- */
  const header = $('.site-header');
  let lastY = scrollY;
  addEventListener('scroll', () => {
    const y = scrollY;
    if (!body.classList.contains('locked')) header.classList.toggle('is-hidden', y > 300 && y > lastY + 4);
    if (y < lastY - 4 || y < 300) header.classList.remove('is-hidden');
    lastY = y;
  }, { passive: true });

  /* ---------- mobile menu ---------- */
  const menuBtn = $('[data-menu]');
  const mnav = $('#mobile-nav');
  menuBtn?.addEventListener('click', () => {
    const open = menuBtn.getAttribute('aria-expanded') !== 'true';
    menuBtn.setAttribute('aria-expanded', open);
    mnav.hidden = !open;
    mnav.classList.toggle('open', open);
    body.classList.toggle('locked', open);
  });

  /* ---------- reveal on scroll ---------- */
  const io = new IntersectionObserver((es) => es.forEach((en) => {
    if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
  }), { rootMargin: '0px 0px -8% 0px' });
  $$('.reveal').forEach((el) => io.observe(el));

  /* ---------- hero: subtle pointer parallax ---------- */
  const art = $('.hero-art');
  if (art && !reduce && matchMedia('(pointer: fine)').matches) {
    const hero = $('.hero');
    hero.addEventListener('pointermove', (ev) => {
      const r = hero.getBoundingClientRect();
      const x = (ev.clientX - r.left) / r.width - .5, y = (ev.clientY - r.top) / r.height - .5;
      art.style.transform = `translate3d(${x * -14}px, ${y * -10}px, 0)`;
      $('.hero-wheel').style.transform = `rotate(${x * 8}deg)`;
    });
    hero.addEventListener('pointerleave', () => { art.style.transform = ''; $('.hero-wheel').style.transform = ''; });
    art.style.transition = 'transform .6s cubic-bezier(.2,.7,.1,1)';
    $('.hero-wheel').style.transition = 'transform .8s cubic-bezier(.2,.7,.1,1)';
  }

  /* ---------- quote: words light up while scrolling ---------- */
  $$('[data-words]').forEach((q) => {
    const words = q.textContent.trim().split(/\s+/);
    q.innerHTML = words.map((w) => `<span class="w">${w}</span>`).join(' ');
    const spans = $$('.w', q);
    const upd = () => {
      const r = q.getBoundingClientRect();
      const p = Math.min(1, Math.max(0, (innerHeight * .85 - r.top) / (r.height + innerHeight * .35)));
      const n = Math.round(p * spans.length);
      spans.forEach((s, i) => s.classList.toggle('on', i < n));
    };
    if (reduce) spans.forEach((s) => s.classList.add('on'));
    else { addEventListener('scroll', upd, { passive: true }); upd(); }
  });

  /* ---------- product rail: drag + progress ---------- */
  $$('[data-rail]').forEach((rail) => {
    const bar = $('[data-rail-progress]');
    const upd = () => {
      const max = rail.scrollWidth - rail.clientWidth;
      const vis = rail.clientWidth / rail.scrollWidth;
      if (bar) { bar.style.width = vis * 100 + '%'; bar.style.left = (max ? rail.scrollLeft / max : 0) * (100 - vis * 100) + '%'; }
    };
    rail.addEventListener('scroll', upd, { passive: true }); addEventListener('resize', upd); upd();
    const step = () => rail.querySelector('.pc').getBoundingClientRect().width + 20;
    $('[data-rail-prev]')?.addEventListener('click', () => rail.scrollBy({ left: -step(), behavior: 'smooth' }));
    $('[data-rail-next]')?.addEventListener('click', () => rail.scrollBy({ left: step(), behavior: 'smooth' }));
    let down = false, sx = 0, sl = 0, moved = 0;
    rail.addEventListener('pointerdown', (e) => { if (e.pointerType !== 'mouse') return; down = true; moved = 0; sx = e.clientX; sl = rail.scrollLeft; });
    addEventListener('pointermove', (e) => { if (!down) return; const dx = e.clientX - sx; moved = Math.abs(dx); if (moved > 5) rail.classList.add('dragging'); rail.scrollLeft = sl - dx; });
    addEventListener('pointerup', () => { if (!down) return; down = false; setTimeout(() => rail.classList.remove('dragging'), 0); });
    rail.addEventListener('keydown', (e) => { if (e.key === 'ArrowRight') rail.scrollBy({ left: step(), behavior: 'smooth' }); if (e.key === 'ArrowLeft') rail.scrollBy({ left: -step(), behavior: 'smooth' }); });
  });

  /* ---------- shop: filter + sort ---------- */
  const grid = $('[data-grid]');
  if (grid) {
    const chips = $$('[data-filter]');
    const count = $('[data-result-count]');
    const apply = (f, push) => {
      if (!chips.some((c) => c.dataset.filter === f)) f = 'all';
      chips.forEach((c) => { const on = c.dataset.filter === f; c.classList.toggle('is-on', on); c.setAttribute('aria-pressed', on); });
      let n = 0;
      $$('.pc', grid).forEach((pc, i) => {
        const show = f === 'all' || pc.dataset.cat === f;
        pc.classList.toggle('is-out', !show);
        pc.classList.remove('is-in');
        if (show) { n++; void pc.offsetWidth; pc.classList.add('is-in'); pc.style.animationDelay = Math.min(n, 12) * 30 + 'ms'; }
      });
      count.textContent = n + (n === 1 ? ' Produkt' : ' Produkte');
      if (push) history.replaceState(null, '', f === 'all' ? location.pathname : '#' + f);
    };
    chips.forEach((c) => c.addEventListener('click', () => apply(c.dataset.filter, true)));
    $('[data-sort]').addEventListener('change', (e) => {
      const v = e.target.value;
      const items = $$('.pc', grid);
      items.sort((a, b) => v === 'asc' ? a.dataset.price - b.dataset.price : v === 'desc' ? b.dataset.price - a.dataset.price : b.dataset.date.localeCompare(a.dataset.date));
      items.forEach((i) => grid.appendChild(i));
    });
    const fromHash = () => apply(decodeURIComponent(location.hash.slice(1)) || 'all', false);
    addEventListener('hashchange', fromHash); fromHash();
  }

  /* ---------- cart (localStorage → Shopify cart permalink) ---------- */
  const KEY = 'nn-cart-v1';
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; } };
  const save = (c) => { try { localStorage.setItem(KEY, JSON.stringify(c)); } catch {} };
  let cart = load();
  const drawer = $('[data-drawer]');
  const toastEl = $('[data-toast]');
  let toastT;
  const toast = (m) => { toastEl.textContent = m; toastEl.classList.add('show'); clearTimeout(toastT); toastT = setTimeout(() => toastEl.classList.remove('show'), 2200); };

  const render = () => {
    const qty = cart.reduce((s, i) => s + i.q, 0);
    const total = cart.reduce((s, i) => s + i.q * i.p, 0);
    $$('[data-cart-count]').forEach((el) => { el.textContent = qty; el.classList.toggle('has', qty > 0); });
    $('[data-cart-count-label]').textContent = qty ? `(${qty})` : '';
    $('[data-cart-total]').textContent = fmt(total);
    const co = $('[data-checkout]');
    co.href = qty ? `${SHOP}/cart/${cart.map((i) => `${i.id}:${i.q}`).join(',')}` : '#';
    co.toggleAttribute('aria-disabled', !qty);
    co.classList.toggle('btn-disabled', !qty);
    const root = body.dataset.root;
    $('[data-cart-items]').innerHTML = qty ? cart.map((i, k) => `
      <div class="line-item">
        <a href="${root}products/${i.h}/"><img src="${i.img}" alt="" width="76" height="76" loading="lazy"></a>
        <div><h3><a href="${root}products/${i.h}/">${i.t}</a></h3><span class="mono">${i.v && i.v !== 'Default Title' ? i.v : ''}</span>
          <div class="li-qty"><button type="button" data-q="${k}" data-d="-1" aria-label="Weniger">−</button><span>${i.q}</span><button type="button" data-q="${k}" data-d="1" aria-label="Mehr">+</button></div></div>
        <div class="li-right"><span>${fmt(i.p * i.q)}</span><button type="button" class="li-remove" data-rm="${k}">Entfernen</button></div>
      </div>`).join('') : `<div class="cart-empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M5 8h14l-1.2 12H6.2L5 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg><p>Dein Warenkorb ist leer.</p><a class="btn btn-ghost" href="${root}collections/all/">Jetzt shoppen</a></div>`;
  };
  const openCart = () => { drawer.hidden = false; requestAnimationFrame(() => drawer.classList.add('open')); body.classList.add('locked'); $('[data-cart-close].icon-btn').focus(); };
  const closeCart = () => { drawer.classList.remove('open'); body.classList.remove('locked'); setTimeout(() => { drawer.hidden = true; }, 450); };
  const add = (item) => {
    const ex = cart.find((i) => i.id === item.id);
    if (ex) ex.q = Math.min(99, ex.q + item.q); else cart.push(item);
    save(cart); render();
    $$('[data-cart-count]').forEach((el) => { el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); });
    toast('Im Warenkorb ✓');
    setTimeout(openCart, 250);
  };
  $$('[data-cart-open]').forEach((b) => b.addEventListener('click', openCart));
  $$('[data-cart-close]').forEach((b) => b.addEventListener('click', closeCart));
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && drawer.classList.contains('open')) closeCart(); });
  $('[data-cart-items]').addEventListener('click', (e) => {
    const q = e.target.closest('[data-q]'), rm = e.target.closest('[data-rm]');
    if (q) { const i = cart[q.dataset.q]; i.q += +q.dataset.d; if (i.q < 1) cart.splice(q.dataset.q, 1); }
    if (rm) cart.splice(rm.dataset.rm, 1);
    if (q || rm) { save(cart); render(); }
  });
  $('[data-checkout]').addEventListener('click', (e) => { if (!cart.length) e.preventDefault(); });
  addEventListener('storage', (e) => { if (e.key === KEY) { cart = load(); render(); } });
  render();

  /* ---------- product page ---------- */
  const pdp = $('[data-product]');
  if (pdp) {
    const P = JSON.parse(pdp.dataset.product);
    const form = $('[data-buy]', pdp);
    const sets = $$('fieldset[data-opt]', form);
    const hint = $('[data-hint]', form);
    const qtyIn = $('[data-qty-input]', form);
    const selected = () => sets.map((fs) => $('input:checked', fs)?.value ?? null);
    const match = (sel) => P.variants.find((v) => v.o.every((o, i) => o === sel[i]));
    const update = () => {
      const sel = selected();
      sets.forEach((fs, i) => {
        $('[data-opt-val]', fs).textContent = sel[i] || '';
        $$('.opt', fs).forEach((lab) => {
          const val = $('input', lab).value;
          const test = sel.slice(); test[i] = val;
          const ok = P.variants.some((v) => v.a && v.o.every((o, k) => k === i ? o === val : (test[k] == null || o === test[k])));
          lab.classList.toggle('is-na', !ok);
        });
      });
      const v = sel.includes(null) ? null : match(sel);
      if (v) $$('[data-price]').forEach((el) => { el.textContent = fmt(v.p); });
      return v;
    };
    form.addEventListener('change', update);
    $$('[data-qty]', form).forEach((b) => b.addEventListener('click', () => { qtyIn.value = Math.max(1, Math.min(20, (+qtyIn.value || 1) + +b.dataset.qty)); }));
    const submit = () => {
      const sel = selected();
      const miss = sets.findIndex((fs, i) => sel[i] == null);
      if (miss > -1) { hint.textContent = `Bitte ${$('legend span', sets[miss]).textContent} wählen.`; sets[miss].scrollIntoView({ block: 'center', behavior: 'smooth' }); return; }
      const v = match(sel);
      if (!v || !v.a) { hint.textContent = 'Diese Variante ist leider ausverkauft.'; return; }
      hint.textContent = '';
      add({ id: v.id, h: P.handle, t: P.title, v: v.t, p: v.p, q: Math.max(1, +qtyIn.value || 1), img: P.img });
    };
    form.addEventListener('submit', (e) => { e.preventDefault(); submit(); });
    update();

    // sticky buy bar on mobile when main button is off-screen
    const sticky = $('[data-sticky-buy]');
    const addBtn = $('[data-add]', form);
    if (sticky && matchMedia('(max-width: 900px)').matches) {
      sticky.hidden = false;
      new IntersectionObserver(([en]) => sticky.classList.toggle('show', !en.isIntersecting && en.boundingClientRect.top < 0)).observe(addBtn);
      $('[data-sticky-add]').addEventListener('click', submit);
    }
    // gallery thumbs follow scroll
    const thumbs = $$('.thumb');
    if (thumbs.length) {
      const tio = new IntersectionObserver((es) => es.forEach((en) => {
        if (en.isIntersecting) thumbs.forEach((t) => t.classList.toggle('is-on', t.getAttribute('href') === '#' + en.target.id));
      }), { threshold: .55 });
      $$('.g-item').forEach((g) => tio.observe(g));
      thumbs.forEach((t) => t.addEventListener('click', (e) => { e.preventDefault(); $(t.getAttribute('href')).scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' }); }));
    }
  }

  /* ---------- custom configurator ---------- */
  const cfgEl = $('[data-config]');
  if (cfgEl) {
    const C = JSON.parse(cfgEl.dataset.config);
    const f = $('[data-cfg-form]');
    const imgEl = $('[data-cfg-img]');
    const val = (n) => $(`input[name="${n}"]:checked`, f).value;
    const find = () => {
      const P = C[val('base')];
      const v = P.variants.find((x) => x.o[0] === val('size') && x.o[1] === val('emb'));
      return { P, v };
    };
    const upd = () => {
      const { P, v } = find();
      $('[data-cfg-price]').textContent = v ? fmt(v.p) : '–';
      if (!imgEl.src.includes(P.img.split('?')[0].split('/').pop())) {
        imgEl.style.opacity = 0;
        setTimeout(() => { imgEl.src = P.img.replace('width=240', 'width=900'); imgEl.style.opacity = 1; }, 200);
      }
      const e = val('emb');
      $('[data-sleeve="l"]').classList.toggle('on', e === 'Links' || e === 'Beide');
      $('[data-sleeve="r"]').classList.toggle('on', e === 'Rechts' || e === 'Beide');
    };
    f.addEventListener('change', upd); upd();
    f.addEventListener('submit', (ev) => {
      ev.preventDefault();
      const { P, v } = find();
      if (!v) return toast('Variante nicht verfügbar');
      add({ id: v.id, h: P.handle, t: P.title, v: v.t, p: v.p, q: 1, img: P.img });
    });
  }

  /* ---------- FAQ toc highlight ---------- */
  const toc = $$('.faq-toc a');
  if (toc.length) {
    const fio = new IntersectionObserver((es) => es.forEach((en) => {
      if (en.isIntersecting) toc.forEach((a) => a.classList.toggle('is-on', a.getAttribute('href') === '#' + en.target.id));
    }), { rootMargin: '-30% 0px -60% 0px' });
    $$('.faq-group').forEach((g) => fio.observe(g));
  }
})();
