import { useEffect, useState } from 'react';
import { addToCart, Cart, checkout, listMenu, listRestaurants, login, MenuItem, Order, register, Restaurant } from './api';

const rupees = (cents: number) => `₹${(cents / 100).toFixed(2)}`;

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [email, setEmail] = useState('customer@example.com');
  const [password, setPassword] = useState('Password123');
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null);
  const [menu, setMenu] = useState<MenuItem[]>([]);
  const [cart, setCart] = useState<Cart | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [message, setMessage] = useState('');

  async function loadRestaurants() {
    const data = await listRestaurants();
    setRestaurants(data);
  }

  useEffect(() => {
    loadRestaurants().catch((error) => setMessage(error.message));
  }, []);

  async function handleLogin() {
    try {
      const response = await login(email, password);
      localStorage.setItem('token', response.access_token);
      setToken(response.access_token);
      setMessage(`Logged in as ${response.user.full_name}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Login failed');
    }
  }

  async function handleRegister() {
    try {
      const response = await register(email, password, 'Web Customer');
      localStorage.setItem('token', response.access_token);
      setToken(response.access_token);
      setMessage(`Registered ${response.user.email}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Registration failed');
    }
  }

  async function openMenu(restaurant: Restaurant) {
    setSelectedRestaurant(restaurant);
    setMenu(await listMenu(restaurant.id));
  }

  async function addItem(item: MenuItem) {
    if (!token) {
      setMessage('Login first');
      return;
    }
    try {
      const updated = await addToCart(token, item.id, 1);
      setCart(updated);
      setMessage(`${item.name} added to cart`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not add item');
    }
  }

  async function placeOrder() {
    if (!token) {
      setMessage('Login first');
      return;
    }
    try {
      const created = await checkout(token, 'Demo Address, Bengaluru');
      setOrder(created);
      setCart(null);
      setMessage(`Order placed: ${created.id}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Checkout failed');
    }
  }

  return (
    <main>
      <header>
        <h1>Food Delivery App</h1>
        <p>FastAPI + SQLAlchemy backend with React UI</p>
      </header>

      <section className="panel">
        <h2>Customer Login</h2>
        <div className="row">
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" />
          <button onClick={handleLogin}>Login</button>
          <button onClick={handleRegister}>Register</button>
          <button onClick={() => { localStorage.removeItem('token'); setToken(''); setCart(null); }}>Logout</button>
        </div>
        {message && <p className="message">{message}</p>}
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Restaurants</h2>
          <button onClick={loadRestaurants}>Refresh</button>
          {restaurants.map((restaurant) => (
            <article className="card" key={restaurant.id}>
              <h3>{restaurant.name}</h3>
              <p>{restaurant.cuisine} · {restaurant.city} · {restaurant.status}</p>
              <p>{restaurant.description}</p>
              <button onClick={() => openMenu(restaurant)}>View menu</button>
            </article>
          ))}
        </div>

        <div className="panel">
          <h2>{selectedRestaurant ? `${selectedRestaurant.name} Menu` : 'Menu'}</h2>
          {menu.map((item) => (
            <article className="card" key={item.id}>
              <h3>{item.name}</h3>
              <p>{item.category} · {rupees(item.price_cents)}</p>
              <p>{item.description}</p>
              <button onClick={() => addItem(item)}>Add</button>
            </article>
          ))}
        </div>

        <div className="panel">
          <h2>Cart</h2>
          {cart?.items.length ? (
            <>
              {cart.items.map((item) => (
                <p key={item.id}>{item.quantity} × {item.name} = {rupees(item.line_total_cents)}</p>
              ))}
              <hr />
              <p>Subtotal: {rupees(cart.subtotal_cents)}</p>
              <p>Delivery: {rupees(cart.delivery_fee_cents)}</p>
              <p>Tax: {rupees(cart.tax_cents)}</p>
              <h3>Total: {rupees(cart.total_cents)}</h3>
              <button onClick={placeOrder}>Checkout</button>
            </>
          ) : <p>No items yet.</p>}
          {order && <p className="message">Latest order {order.id}: {order.status}</p>}
        </div>
      </section>
    </main>
  );
}
