import { Minus, Plus } from "lucide-react";
import { useState } from "react";

import { createOrder } from "../../lib/api/orders";
import { formatCurrency } from "../../lib/format";
import type { Session } from "../../lib/session";
import { useCartStore } from "../../store/cart";
import { Button } from "../ui/Button";
import { Sheet } from "../ui/Sheet";

type CartSheetProps = {
  session: Session | null;
  onRequireSignIn: () => void;
};

export function CartSheet({ session, onRequireSignIn }: CartSheetProps) {
  const items = useCartStore((state) => state.items);
  const isOpen = useCartStore((state) => state.isOpen);
  const closeCart = useCartStore((state) => state.closeCart);
  const clearCart = useCartStore((state) => state.clearCart);
  const setQuantity = useCartStore((state) => state.setQuantity);
  const subtotal = useCartStore((state) => state.subtotal());
  const [checkoutStatus, setCheckoutStatus] = useState("Ready for COD checkout");
  const [paymentMethod, setPaymentMethod] = useState<"cod" | "card" | "upi">("cod");

  async function checkout() {
    if (!session) {
      setCheckoutStatus("Sign in to continue checkout");
      onRequireSignIn();
      return;
    }
    if (paymentMethod !== "cod") {
      setCheckoutStatus("Select Cash on Delivery to continue");
      return;
    }
    setCheckoutStatus("Checking final quantities and prices...");
    try {
      const order = await createOrder({ items, paymentMethod, options: { token: session.accessToken } });
      setCheckoutStatus(`COD order ${order.id} ${order.status}`);
      clearCart();
    } catch (error) {
      setCheckoutStatus(error instanceof Error ? error.message : "Checkout failed; cart kept locally");
    }
  }

  return (
    <Sheet className="cart-drawer" eyebrow="Cart" isOpen={isOpen} onClose={closeCart} title="Shopping cart">
      {items.length === 0 ? (
        <p className="empty-cart">Your cart is ready for service-backed catalog items.</p>
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
                    <Minus aria-hidden="true" />
                  </button>
                  <span>{item.quantity}</span>
                  <button
                    type="button"
                    onClick={() => setQuantity(item.product.id, item.quantity + 1)}
                    aria-label={`Increase ${item.product.name}`}
                  >
                    <Plus aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="cart-summary">
        <div className="payment-methods" aria-label="Payment method">
          <label>
            <input
              type="radio"
              name="payment-method"
              value="cod"
              checked={paymentMethod === "cod"}
              onChange={() => setPaymentMethod("cod")}
            />
            <span>Cash on Delivery</span>
          </label>
          <label className="disabled-payment">
            <input type="radio" name="payment-method" value="card" disabled />
            <span>Card</span>
          </label>
          <label className="disabled-payment">
            <input type="radio" name="payment-method" value="upi" disabled />
            <span>UPI</span>
          </label>
        </div>
        <div>
          <span>Subtotal</span>
          <strong>{formatCurrency(subtotal)}</strong>
        </div>
        <Button variant="primary" onClick={checkout}>
          Checkout COD
        </Button>
        <Button variant="secondary" onClick={closeCart}>
          Continue shopping
        </Button>
        <p className="checkout-status" aria-live="polite">
          {checkoutStatus}
        </p>
      </div>
    </Sheet>
  );
}
