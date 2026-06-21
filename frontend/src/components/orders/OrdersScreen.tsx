import { ClipboardList } from "lucide-react";
import { useState } from "react";

import { formatCurrency } from "../../lib/format";
import type { Order } from "../../lib/api/orders";
import type { Session } from "../../lib/session";

type OrdersScreenProps = {
  orders: Order[];
  session: Session | null;
  onRequireSignIn: () => void;
};

export function OrdersScreen({ orders, session, onRequireSignIn }: OrdersScreenProps) {
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(orders[0]?.id ?? null);
  const selectedOrder = orders.find((order) => order.id === selectedOrderId) ?? orders[0];

  return (
    <section className="orders-screen" id="orders">
      <div className="section-heading">
        <div>
          <h1>Orders</h1>
          <p>
            Select an order to inspect line items, status, totals, and checkout details from the
            gateway order API.
          </p>
        </div>
        <ClipboardList aria-hidden="true" />
      </div>

      {!session ? (
        <div className="orders-auth-panel">
          <strong>Sign in to view your orders</strong>
          <span>Order history is loaded through the gateway after authentication.</span>
          <button type="button" onClick={onRequireSignIn}>
            Sign in
          </button>
        </div>
      ) : null}

      <div className="orders-layout">
        <div className="order-grid" role="list" aria-label="Orders">
          {orders.length > 0 ? (
            orders.map((order) => (
              <button
                className={selectedOrder?.id === order.id ? "active" : ""}
                key={order.id}
                type="button"
                role="listitem"
                onClick={() => setSelectedOrderId(order.id)}
              >
                <span>{order.id}</span>
                <strong>{formatCurrency(order.total)}</strong>
                <small>{order.status}</small>
              </button>
            ))
          ) : (
            <div className="empty-state compact">
              <strong>No orders yet</strong>
              <span>Your COD orders will appear here after checkout.</span>
            </div>
          )}
        </div>

        <article className="order-detail">
          {selectedOrder ? (
            <>
              <div>
                <span>Order detail</span>
                <h2>{selectedOrder.id}</h2>
              </div>
              <dl>
                <div>
                  <dt>Status</dt>
                  <dd>{selectedOrder.status}</dd>
                </div>
                <div>
                  <dt>Total</dt>
                  <dd>{formatCurrency(selectedOrder.total)}</dd>
                </div>
                <div>
                  <dt>Lines</dt>
                  <dd>{selectedOrder.lines.length}</dd>
                </div>
              </dl>
              <div className="order-lines">
                {selectedOrder.lines.map((line) => (
                  <div key={`${selectedOrder.id}-${line.product_id}`}>
                    <span>{line.product_id}</span>
                    <strong>
                      {line.quantity} x {formatCurrency(line.unit_price)}
                    </strong>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state compact">
              <strong>Select an order</strong>
              <span>Click an order card to open the detailed view.</span>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
