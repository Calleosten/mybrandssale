// Byt ut mot din deployade backend-URL (t.ex. Render, Railway, Fly.io)
export const API_BASE_URL = "https://din-backend.example.com";

export async function fetchProducts({ brand, onSaleOnly } = {}) {
  const params = new URLSearchParams();
  if (brand) params.append("brand", brand);
  if (onSaleOnly) params.append("on_sale_only", "true");

  const res = await fetch(`${API_BASE_URL}/products?${params.toString()}`);
  if (!res.ok) throw new Error("Kunde inte hämta produkter");
  return res.json();
}

export async function fetchBrands() {
  const res = await fetch(`${API_BASE_URL}/brands`);
  if (!res.ok) throw new Error("Kunde inte hämta märken");
  return res.json();
}

export async function fetchWatchlist(userId) {
  const res = await fetch(`${API_BASE_URL}/watchlist/${userId}`);
  if (!res.ok) throw new Error("Kunde inte hämta bevakningslista");
  return res.json();
}

export async function addToWatchlist(userId, productId, thresholdPercent = 15) {
  const res = await fetch(`${API_BASE_URL}/watchlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      product_id: productId,
      notify_threshold_percent: thresholdPercent,
    }),
  });
  if (!res.ok) throw new Error("Kunde inte lägga till bevakning");
  return res.json();
}

export async function registerDeviceToken(userId, fcmToken) {
  const res = await fetch(`${API_BASE_URL}/device-tokens`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, fcm_token: fcmToken }),
  });
  if (!res.ok) throw new Error("Kunde inte registrera enhet för notiser");
  return res.json();
}
