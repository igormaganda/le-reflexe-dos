const products = {
  sos: { name: "SOS Lumbago — 7 jours", price: 12.9 },
  solide: { name: "Dos Solide — 28 jours", price: 34.9 },
  bundle: { name: "Pack Reprendre confiance", price: 44.9 },
  video: { name: "Programme vidéo guidé", price: 79 }
};

let cart = JSON.parse(localStorage.getItem("reflexe-dos-cart") || "[]");

const euro = value => new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" }).format(value);

function saveCart() {
  localStorage.setItem("reflexe-dos-cart", JSON.stringify(cart));
  renderCart();
}

function renderCart() {
  const count = document.querySelector("[data-cart-count]");
  const list = document.querySelector("[data-cart-items]");
  const total = document.querySelector("[data-cart-total]");
  if (count) count.textContent = cart.length;
  if (!list || !total) return;
  list.innerHTML = cart.length
    ? cart.map((id, index) => `<div class="cart-item"><div><strong>${products[id].name}</strong><br><span class="small muted">Accès numérique individuel</span></div><div><strong>${euro(products[id].price)}</strong><br><button class="link-arrow" data-remove="${index}" type="button">Retirer</button></div></div>`).join("")
    : `<p class="muted">Votre panier est vide. Choisissez le support qui correspond à votre étape.</p>`;
  total.textContent = euro(cart.reduce((sum, id) => sum + products[id].price, 0));
}

function toggleCart(open) {
  document.querySelector("[data-cart-panel]")?.classList.toggle("is-open", open);
  document.querySelector("[data-backdrop]")?.classList.toggle("is-open", open);
  document.body.style.overflow = open ? "hidden" : "";
}

function toast(message) {
  const el = document.querySelector("[data-toast]");
  if (!el) return;
  el.textContent = message;
  el.classList.add("is-visible");
  window.clearTimeout(window.toastTimer);
  window.toastTimer = window.setTimeout(() => el.classList.remove("is-visible"), 3200);
}

document.addEventListener("click", event => {
  const add = event.target.closest("[data-add]");
  const remove = event.target.closest("[data-remove]");
  if (add) {
    cart.push(add.dataset.add);
    saveCart();
    toast(`${products[add.dataset.add].name} ajouté au panier.`);
    toggleCart(true);
  }
  if (remove) {
    cart.splice(Number(remove.dataset.remove), 1);
    saveCart();
  }
  if (event.target.closest("[data-cart-open]")) toggleCart(true);
  if (event.target.closest("[data-cart-close]") || event.target.matches("[data-backdrop]")) toggleCart(false);
  if (event.target.closest("[data-menu]")) document.querySelector("[data-nav-links]")?.classList.toggle("is-open");
});

document.querySelectorAll("form[data-demo-form]").forEach(form => {
  form.addEventListener("submit", event => {
    event.preventDefault();
    const consent = form.querySelector("input[type=checkbox]");
    if (consent && !consent.checked) {
      toast("Cochez la case de consentement pour continuer.");
      return;
    }
    form.reset();
    toast(form.dataset.success || "Merci. Votre demande a bien été préparée.");
  });
});

document.querySelector("[data-checkout]")?.addEventListener("click", () => {
  toast("Démo statique : le paiement Stripe sera connecté lors du passage en production.");
});

renderCart();
