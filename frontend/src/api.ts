export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type Restaurant = {
  id: string;
  name: string;
  description?: string;
  cuisine: string;
  address: string;
  city: string;
  status: string;
  rating: number;
  delivery_fee_cents: number;
};

export type MenuItem = {
  id: string;
  restaurant_id: string;
  name: string;
  description?: string;
  category: string;
  price_cents: number;
  is_available: boolean;
};

export type Cart = {
  id: string | null;
  restaurant_id: string | null;
  items: Array<{
    id: string;
    menu_item_id: string;
    name: string;
    unit_price_cents: number;
    quantity: number;
    line_total_cents: number;
  }>;
  subtotal_cents: number;
  delivery_fee_cents: number;
  tax_cents: number;
  total_cents: number;
};

export type Order = {
  id: string;
  status: string;
  total_cents: number;
  payment_method: string;
  created_at: string;
};

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }
  return body as T;
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
}

export function register(email: string, password: string, fullName: string): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName, role: 'CUSTOMER' })
  });
}

export function listRestaurants(): Promise<Restaurant[]> {
  return request<Restaurant[]>('/restaurants?limit=20');
}

export function listMenu(restaurantId: string): Promise<MenuItem[]> {
  return request<MenuItem[]>(`/restaurants/${restaurantId}/menu`);
}

export function getCart(token: string): Promise<Cart> {
  return request<Cart>('/cart', {}, token);
}

export function addToCart(token: string, menuItemId: string, quantity = 1): Promise<Cart> {
  return request<Cart>('/cart/items', {
    method: 'POST',
    body: JSON.stringify({ menu_item_id: menuItemId, quantity })
  }, token);
}

export function checkout(token: string, address: string): Promise<Order> {
  return request<Order>('/orders', {
    method: 'POST',
    headers: { 'X-Idempotency-Key': `web-${crypto.randomUUID()}` },
    body: JSON.stringify({ delivery_address: address, payment_method: 'UPI' })
  }, token);
}
