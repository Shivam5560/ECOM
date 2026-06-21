import type { CSSProperties } from "react";

import { formatCurrency } from "../../lib/format";
import { useCartStore } from "../../store/cart";
import type { Product } from "../../types";

export function ProductCard({ product }: { product: Product }) {
  const addItem = useCartStore((state) => state.addItem);

  return (
    <article className="product-card">
      <div className="product-image" style={{ "--accent": product.accent } as CSSProperties}>
        <img src={product.image} alt={product.name} />
        <span>{product.stock} left</span>
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
        <button type="button" onClick={() => addItem(product)} disabled={product.stock <= 0}>
          Add to cart
        </button>
      </div>
    </article>
  );
}
