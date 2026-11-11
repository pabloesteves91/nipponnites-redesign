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
          <div class="flex flex-col items-center justify-center h-full gap-4 opacity-30">
            <span class="material-symbols-outlined text-6xl">shopping_bag</span>
            <p class="font-headline uppercase font-bold tracking-tighter">Your bag is empty</p>
          </div>`;
      } else {
        itemsEl.innerHTML = cart.items.map(item => {
          const imgUrl = item.featured_image ? shopifyImgUrl(item.featured_image.url, '200x200') : '';
          const qty = String(item.quantity).padStart(2, '0');
          const varLine = (item.variant_title && item.variant_title !== 'Default Title')
            ? `<span style="font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.1em;display:block;margin-top:0.25rem;">${item.variant_title}</span>`
            : '';
          return `
            <div class="flex gap-4 items-start" data-cart-item="${item.key}">
              <a href="${item.url}" class="w-24 h-24 flex-shrink-0 overflow-hidden block" style="background:#1b1b1b;">
                ${imgUrl ? `<img src="${imgUrl}" alt="${item.title}" class="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-500">` : ''}
              </a>
              <div class="flex flex-col flex-grow">
                <div class="flex justify-between items-start gap-2">
                  <a href="${item.url}" class="font-headline font-bold text-sm tracking-tighter uppercase leading-tight hover:text-primary transition-colors">${item.product_title}</a>
                  <button onclick="cartRemoveItem('${item.key}')" class="text-white/20 hover:text-primary transition-colors flex-shrink-0" aria-label="Remove">
                    <span class="material-symbols-outlined text-sm">delete</span>
                  </button>
                </div>
                ${varLine}
                <div class="mt-4 flex justify-between items-center">
                  <div class="flex items-center gap-3 px-3 py-1" style="background:#1b1b1b;">
                    <button onclick="cartUpdateItem('${item.key}', ${item.quantity - 1})" class="text-white/40 hover:text-white transition-colors" aria-label="Decrease">
                      <span class="material-symbols-outlined" style="font-size:14px">remove</span>
                    </button>
                    <span class="font-headline font-bold text-xs w-5 text-center" data-item-qty="${item.key}">${qty}</span>
                    <button onclick="cartUpdateItem('${item.key}', ${item.quantity + 1})" class="text-white/40 hover:text-white transition-colors" aria-label="Increase">
                      <span class="material-symbols-outlined" style="font-size:14px">add</span>
                    </button>
                  </div>
                  <span class="font-headline font-bold text-primary" data-item-price="${item.key}">${formatMoney(item.final_line_price)}</span>
                </div>
              </div>
            </div>`;
        }).join('');
      }
    }

    // Update CTA button
    const ctaEl = document.getElementById('cart-drawer-cta');
    if (ctaEl) {
      ctaEl.innerHTML = cart.item_count > 0
        ? `<a href="/checkout" class="block w-full py-5 bg-gradient-to-br from-[#ffb4a9] to-[#fb5a48] text-[#410000] font-headline font-black uppercase text-center tracking-tighter text-lg hover:brightness-110 active:scale-[0.98] transition-all duration-300">PROCEED TO CHECKOUT</a>`
        : `<a href="/collections/all" class="block w-full py-5 bg-[#353535] text-white/60 font-headline font-black uppercase text-center tracking-tighter text-lg hover:bg-[#ffb4a9] hover:text-[#410000] transition-all">SHOP NOW</a>`;
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
  btn.textContent = '✓ Added!';
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
