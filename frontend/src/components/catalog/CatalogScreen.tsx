import { CheckCircle2, PackageCheck, Search, Truck } from "lucide-react";
import { useMemo, useState } from "react";

import { formatCurrency } from "../../lib/format";
import type { Product } from "../../types";
import { ProductCard } from "./ProductCard";

type CatalogScreenProps = {
  products: Product[];
  status: string;
};

export function CatalogScreen({ products, status }: CatalogScreenProps) {
  const [activeCategory, setActiveCategory] = useState("All");
  const [query, setQuery] = useState("");
  const heroProduct = products[0];
  const secondary = products[1];
  const categories = useMemo(
    () => ["All", ...Array.from(new Set(products.map((product) => product.category)))],
    [products],
  );
  const filteredProducts = products.filter((product) => {
    const matchesCategory = activeCategory === "All" || product.category === activeCategory;
    const matchesQuery = `${product.name} ${product.category} ${product.description}`
      .toLowerCase()
      .includes(query.toLowerCase());
    return matchesCategory && matchesQuery;
  });

  return (
    <section className="screen-stack" id="catalog">
      <div className="hero banner">
        <div className="banner-copy">
          <h1>Gateway storefront</h1>
          <p>
            Shop service-backed products with a cleaner catalog flow, COD checkout, and gateway
            powered order handling.
          </p>
          <div className="hero-actions">
            <a className="primary-button" href="#catalog-products">
              Shop collection
            </a>
          </div>
        </div>
        <div className="motion-board" aria-label="Animated commerce banner">
          <div className="motion-ribbon ribbon-a" />
          <div className="motion-ribbon ribbon-b" />
          <div className="metric-tile tile-orders">
            <PackageCheck aria-hidden="true" />
            <span>Quantity check</span>
            <strong>Live</strong>
          </div>
          <div className="metric-tile tile-payment">
            <CheckCircle2 aria-hidden="true" />
            <span>Payment mode</span>
            <strong>COD</strong>
          </div>
          <div className="metric-tile tile-dispatch">
            <Truck aria-hidden="true" />
            <span>Gateway</span>
            <strong>Ready</strong>
          </div>
          {heroProduct ? (
            <article className="hero-product">
              <img src={heroProduct.image} alt={heroProduct.name} />
              <div>
                <p>{heroProduct.category}</p>
                <h2>{heroProduct.name}</h2>
                <strong>{formatCurrency(heroProduct.price)}</strong>
              </div>
            </article>
          ) : null}
          {secondary ? (
            <article className="hero-mini-product">
              <img src={secondary.image} alt="" />
              <span>{secondary.name}</span>
            </article>
          ) : null}
        </div>
      </div>

      <section className="collections" id="catalog-products">
        <div className="section-heading">
          <div>
            <h2>Catalog</h2>
            <p>{status}</p>
          </div>
          <label className="search-control">
            <Search aria-hidden="true" />
            <span className="sr-only">Search products</span>
            <input
              type="search"
              placeholder="Search catalog"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
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
        <div className="product-grid">
          {filteredProducts.length > 0 ? (
            filteredProducts.map((product) => <ProductCard key={product.id} product={product} />)
          ) : (
            <div className="empty-state">
              <strong>No catalog products found</strong>
              <span>
                {products.length === 0
                  ? "Connect the product API or add products from admin."
                  : "Try a different search or category."}
              </span>
            </div>
          )}
        </div>
      </section>
    </section>
  );
}
