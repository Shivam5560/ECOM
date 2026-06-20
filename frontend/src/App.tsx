import { Heart, Minus, Plus, Search, ShoppingBag, UserRound, X } from "lucide-react";
import { useMemo, useState } from "react";

import { categories, products } from "./data/catalog";
import { formatCurrency } from "./lib/format";
import { createOrder } from "./lib/api/orders";
import { useCartStore } from "./store/cart";
import type { Product } from "./types";

function Header() {
  const itemCount = useCartStore((state) => state.itemCount());
  const openCart = useCartStore((state) => state.openCart);

  return (
    <header className="site-header">
      <a className="brand" href="#top" aria-label="ECOM home">
        ECOM
      </a>
      <nav className="main-nav" aria-label="Primary navigation">
        <a href="#new">New</a>
        <a href="#collections">Collections</a>
        <a href="#orders">Orders</a>
        <a href="#account">Account</a>
      </nav>
      <div className="header-actions">
        <label className="search-control">
          <Search size={18} aria-hidden="true" />
          <span className="sr-only">Search products</span>
          <input type="search" placeholder="Search essentials" />
        </label>
        <button className="icon-button" type="button" aria-label="Account">
          <UserRound size={19} aria-hidden="true" />
        </button>
        <button className="cart-button" type="button" onClick={openCart}>
          <ShoppingBag size={19} aria-hidden="true" />
          <span>Cart</span>
          <strong>{itemCount}</strong>
        </button>
      </div>
    </header>
  );
}

function Hero() {
  const addItem = useCartStore((state) => state.addItem);
  const heroProduct = products[0];

  return (
    <section className="hero" id="top">
      <div className="hero-copy">
        <h1>Curated essentials, delivered fast</h1>
        <p>
          Premium everyday objects selected for calm homes, sharp desks, and
          lighter travel. Discover limited drops from independent makers.
        </p>
        <div className="hero-actions">
          <button className="primary-button" type="button" onClick={() => addItem(heroProduct)}>
            Shop new arrivals
          </button>
          <a className="secondary-link" href="#collections">
            Explore collections
          </a>
        </div>
      </div>
      <div className="hero-showcase" aria-label="Featured product">
        <img src={heroProduct.image} alt={heroProduct.name} />
        <div className="showcase-panel">
          <span>{heroProduct.inventory}</span>
          <strong>{heroProduct.name}</strong>
          <p>{formatCurrency(heroProduct.price)}</p>
        </div>
      </div>
    </section>
  );
}

function ProductCard({ product }: { product: Product }) {
  const addItem = useCartStore((state) => state.addItem);

  return (
    <article className="product-card">
      <div className="product-image" style={{ "--accent": product.accent } as React.CSSProperties}>
        <img src={product.image} alt={product.name} />
        <button type="button" aria-label={`Save ${product.name}`}>
          <Heart size={17} aria-hidden="true" />
        </button>
      </div>
      <div className="product-details">
        <div>
          <p>{product.category}</p>
          <h3>{product.name}</h3>
        </div>
        <strong>{formatCurrency(product.price)}</strong>
      </div>
      <p className="product-description">{product.description}</p>
      <div className="product-footer">
        <span>{product.rating.toFixed(1)} rating</span>
        <button type="button" onClick={() => addItem(product)}>
          Add to cart
        </button>
      </div>
    </article>
  );
}

function Collections() {
  const [activeCategory, setActiveCategory] = useState<(typeof categories)[number]>("All");
  const filteredProducts = useMemo(
    () =>
      activeCategory === "All"
        ? products
        : products.filter((product) => product.category === activeCategory),
    [activeCategory],
  );

  return (
    <section className="collections" id="collections">
      <div className="section-heading">
        <div>
          <h2>Featured drops</h2>
          <p>Objects with refined materials, fast fulfillment, and useful details.</p>
        </div>
        <div className="category-tabs" aria-label="Product categories">
          {categories.map((category) => (
            <button
              className={activeCategory === category ? "active" : ""}
              key={category}
              type="button"
              onClick={() => setActiveCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>
      </div>
      <div className="product-grid">
        {filteredProducts.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      <ProfessionalGrid />
    </section>
  );
}

function ProfessionalGrid() {
  const rows = products.map((product) => ({
    id: product.id,
    product: product.name,
    category: product.category,
    price: formatCurrency(product.price),
    inventory: product.inventory,
    rating: product.rating.toFixed(1),
  }));

  return (
    <section className="professional-grid" aria-labelledby="grid-title">
      <div className="grid-toolbar">
        <div>
          <h3 id="grid-title">Product grid</h3>
          <p>API-ready columns, filters, stable row actions, and checkout metadata.</p>
        </div>
        <div className="grid-filters">
          <input type="search" placeholder="Search catalog" aria-label="Search catalog" />
          <select aria-label="Sort products" defaultValue="featured">
            <option value="featured">Featured</option>
            <option value="price">Price</option>
            <option value="rating">Rating</option>
          </select>
        </div>
      </div>
      <div className="grid-table" role="table" aria-label="Products">
        <div className="grid-row grid-head" role="row">
          <span role="columnheader">Product</span>
          <span role="columnheader">Category</span>
          <span role="columnheader">Price</span>
          <span role="columnheader">Inventory</span>
          <span role="columnheader">Rating</span>
          <span role="columnheader">Action</span>
        </div>
        {rows.map((row) => (
          <div className="grid-row" role="row" key={row.id}>
            <span role="cell">{row.product}</span>
            <span role="cell">{row.category}</span>
            <span role="cell">{row.price}</span>
            <span role="cell">{row.inventory}</span>
            <span role="cell">{row.rating}</span>
            <button type="button">View</button>
          </div>
        ))}
      </div>
    </section>
  );
}

function AccountPanel() {
  return (
    <section className="account-panel" id="account">
      <div>
        <h2>Account</h2>
        <p>
          Sign in to sync your profile, save delivery preferences, and prepare
          for order history once the order service is available.
        </p>
      </div>
      <form className="auth-form">
        <label>
          Email
          <input type="email" placeholder="buyer@ecom.dev" />
        </label>
        <label>
          Password
          <input type="password" placeholder="Password" />
        </label>
        <button type="button">Continue</button>
      </form>
    </section>
  );
}

function CartDrawer() {
  const items = useCartStore((state) => state.items);
  const isOpen = useCartStore((state) => state.isOpen);
  const closeCart = useCartStore((state) => state.closeCart);
  const setQuantity = useCartStore((state) => state.setQuantity);
  const subtotal = useCartStore((state) => state.subtotal());
  const [checkoutStatus, setCheckoutStatus] = useState("Ready for checkout");

  if (!isOpen) {
    return null;
  }

  return (
    <div className="drawer-backdrop">
      <aside className="cart-drawer" role="dialog" aria-label="Shopping cart" aria-modal="true">
        <div className="drawer-header">
          <div>
            <p>Cart</p>
            <h2>Shopping cart</h2>
          </div>
          <button className="icon-button" type="button" onClick={closeCart} aria-label="Close cart">
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        {items.length === 0 ? (
          <p className="empty-cart">Your cart is ready for the next drop.</p>
        ) : (
          <div className="cart-items">
            {items.map((item) => (
              <div className="cart-row" key={item.product.id}>
                <img src={item.product.image} alt="" />
                <div>
                  <h3>{item.product.name}</h3>
                  <p>{formatCurrency(item.product.price)}</p>
                  <div className="quantity-control">
                    <button
                      type="button"
                      onClick={() => setQuantity(item.product.id, item.quantity - 1)}
                      aria-label={`Decrease ${item.product.name}`}
                    >
                      <Minus size={14} aria-hidden="true" />
                    </button>
                    <span>{item.quantity}</span>
                    <button
                      type="button"
                      onClick={() => setQuantity(item.product.id, item.quantity + 1)}
                      aria-label={`Increase ${item.product.name}`}
                    >
                      <Plus size={14} aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="cart-summary">
          <div>
            <span>Subtotal</span>
            <strong>{formatCurrency(subtotal)}</strong>
          </div>
          <button
            type="button"
            onClick={async () => {
              setCheckoutStatus("Creating order...");
              try {
                const order = await createOrder({ userId: "buyer-1", items });
                setCheckoutStatus(`Order ${order.id} ${order.status}`);
              } catch {
                setCheckoutStatus("Order API unavailable; cart kept locally");
              }
            }}
          >
            Checkout
          </button>
          <p className="checkout-status" aria-live="polite">{checkoutStatus}</p>
        </div>
      </aside>
    </div>
  );
}

export default function App() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Collections />
        <AccountPanel />
      </main>
      <CartDrawer />
    </>
  );
}
