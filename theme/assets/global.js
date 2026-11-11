// ── Cart Drawer ───────────────────────────────────────────────────────────────

function openCartDrawer() {
  const drawer = document.getElementById('cart-drawer');
  const backdrop = document.getElementById('cart-backdrop');
  if (!drawer) return;
  drawer.classList.remove('translate-x-full');
  if (backdrop) {
    backdrop.classList.remove('opacity-0', 'pointer-events-none');
  }
  document.body.style.overflow = 'hidden';
}

function closeCartDrawer() {
  const drawer = document.getElementById('cart-drawer');
  const backdrop = document.getElementById('cart-backdrop');
  if (!drawer) return;
  drawer.classList.add('translate-x-full');
  if (backdrop) {
    backdrop.classList.add('opacity-0', 'pointer-events-none');
  }
  document.body.style.overflow = '';
}

function formatMoney(cents) {
  const fmt = window.__moneyFormat || '{{amount}}';
  const amount = (cents / 100).toFixed(2);
  return fmt
    .replace('{{amount}}', amount)
    .replace('{{amount_no_decimals}}', Math.floor(cents / 100))
    .replace('{{amount_with_comma_separator}}', amount.replace('.', ','));
}

async function cartUpdateItem(key, quantity) { /* Shopify vergibt nach Mengenaenderungen neue Artikel-Schluessel (z. B. wegen Rabatten) - deshalb Warenkorb nach jeder Aenderung komplett neu rendern */ try { const res = await fetch('/cart/change.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: key, quantity: Math.max(0, quantity) }) }); if (!res.ok) console.warn('Cart change failed:', res.status); } catch (e) { console.error('Cart update failed:', e); } await refreshAndOpenCart(); }

function cartRemoveItem(key) {
  cartUpdateItem(key, 0);
}

// Open drawer after add-to-cart
document.addEventListener('cart:updated', openCartDrawer);

// ── Cart Drawer AJAX Refresh ───────────────────────────────────────────────

function shopifyImgUrl(url, size) {
  if (!url) return '';
  return url.replace(/(\.[a-z]+)(\?|$)/, '_' + size + '$1$2');
}

async function refreshAndOpenCart() {
  try {
    const res = await fetch('/cart.js');
    const cart = await res.json();

    // Update count badge
    document.querySelectorAll('[data-cart-count]').forEach(el => {
      el.textContent = cart.item_count;
      el.hidden = cart.item_count === 0;
    });

    // Update subtotal
    const subtotalEl = document.getElementById('cart-drawer-subtotal');
    if (subtotalEl) subtotalEl.textContent = formatMoney(cart.total_price);

    // Rebuild items list
    const itemsEl = document.getElementById('cart-drawer-items');
    if (itemsEl) {
      if (cart.item_count === 0) {
        itemsEl.innerHTML = `
          <div class="nn-zettel__leer">
            <p class="nn-h4">Dein Warenkorb ist leer</p>
            <p class="nn-klein">Schau dich in den Drops um oder lass dein eigenes Auto zeichnen.</p>
          </div>`;
      } else {
        itemsEl.innerHTML = cart.items.map(item => {
          const imgUrl = item.featured_image ? shopifyImgUrl(item.featured_image.url, '200x200') : '';
          const varLine = (item.variant_title && item.variant_title !== 'Default Title')
            ? `<span class="nn-zettel__variante">${item.variant_title}</span>` : '';
          return `
            <div class="nn-zettel__posten" data-cart-item="${item.key}">
              <a href="${item.url}">${imgUrl ? `<img src="${imgUrl}" alt="${item.product_title}" width="84" height="84" loading="lazy">` : ''}</a>
              <div>
                <a href="${item.url}" class="nn-zettel__titel">${item.product_title}</a>
                ${varLine}
                <div class="nn-zettel__zeile">
                  <div class="nn-zettel__menge">
                    <button type="button" onclick="cartUpdateItem('${item.key}', ${item.quantity - 1})" aria-label="Menge verringern">−</button>
                    <span data-item-qty="${item.key}">${item.quantity}</span>
                    <button type="button" onclick="cartUpdateItem('${item.key}', ${item.quantity + 1})" aria-label="Menge erhöhen">+</button>
                  </div>
                  <strong data-item-price="${item.key}">${formatMoney(item.final_line_price)}</strong>
                </div>
                <button type="button" class="nn-zettel__weg" onclick="cartRemoveItem('${item.key}')" aria-label="${item.product_title} entfernen">Entfernen</button>
              </div>
            </div>`;
        }).join('');
      }
    }

    // Update CTA button
    const ctaEl = document.getElementById('cart-drawer-cta');
    if (ctaEl) {
      ctaEl.innerHTML = cart.item_count > 0
        ? `<a href="/checkout" class="nn-btn nn-btn--marker nn-btn--voll">Zur Kasse</a>`
        : `<a href="/collections/all" class="nn-btn nn-btn--voll">Drops ansehen</a>`;
    }
  } catch(e) { console.error('Cart refresh failed:', e); }

  openCartDrawer();
}

// ── Cart Count ────────────────────────────────────────────────────────────────

async function updateCartCount() {
  try {
    const res = await fetch('/cart.js');
    const cart = await res.json();
    document.querySelectorAll('[data-cart-count]').forEach(el => {
      el.textContent = cart.item_count;
      el.hidden = cart.item_count === 0;
    });
  } catch(e) {}
}
document.addEventListener('DOMContentLoaded', updateCartCount);
const menuBtn = document.getElementById('mobile-menu-btn');
const mobileNav = document.getElementById('mobile-nav');
if (menuBtn && mobileNav) {
  menuBtn.addEventListener('click', () => {
    const open = mobileNav.classList.toggle('hidden');
    menuBtn.setAttribute('aria-expanded', String(!open));
  });
}
const dismissBtn = document.getElementById('dismiss-announcement');
const annBar = document.getElementById('announcement-bar');
if (dismissBtn && annBar) {
  dismissBtn.addEventListener('click', () => { annBar.style.display = 'none'; sessionStorage.setItem('ann-dismissed','1'); });
  if (sessionStorage.getItem('ann-dismissed')) annBar.style.display = 'none';
}
document.addEventListener('submit', async (e) => {
  const form = e.target.closest('form[action="/cart/add"]');
  if (!form) return;
  e.preventDefault();
  const btn = form.querySelector('[type="submit"]');
  const orig = btn.textContent;
  btn.textContent = 'Hinzugefügt';
  btn.disabled = true;
  try { await fetch('/cart/add.js', { method:'POST', body: new FormData(form) }); await refreshAndOpenCart(); } catch(_) {}
  setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 1500);
});

// ── Scroll to Top (Mobile) ────────────────────────────────────────────────────
(function () {
  const btn = document.getElementById('scroll-top-btn');
  if (!btn) return;
  window.addEventListener('scroll', function () {
    if (window.scrollY > 300) {
      btn.classList.remove('opacity-0', 'pointer-events-none');
    } else {
      btn.classList.add('opacity-0', 'pointer-events-none');
    }
  }, { passive: true });
})();
