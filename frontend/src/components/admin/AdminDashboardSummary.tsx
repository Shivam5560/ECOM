import { BarChart3, ImagePlus, TrendingUp } from "lucide-react";

import { formatCurrency } from "../../lib/format";
import type { Product } from "../../types";

export function AdminDashboardSummary({ products }: { products: Product[] }) {
  const totalStock = products.reduce((sum, product) => sum + product.stock, 0);
  const lowStock = products.filter((product) => product.stock <= 6).length;
  const inventoryValue = products.reduce((sum, product) => sum + product.price * product.stock, 0);
  const maxStock = Math.max(...products.map((product) => product.stock), 1);
  const chartProducts = products.slice(0, 6);

  return (
    <section className="admin-dashboard" id="dashboard">
      <aside className="admin-sidebar">
        <strong>ECOM</strong>
        <span className="active">Dashboard</span>
        <span>Products</span>
        <span>Collections</span>
        <span>Orders</span>
        <span>Customers</span>
      </aside>
      <div className="admin-main-panel">
        <div className="admin-title-row">
          <div>
            <h1>Product operations</h1>
            <p>Admin-only view for dashboards, analysis, product images, and catalog controls.</p>
          </div>
          <button className="primary-button" type="button">
            <ImagePlus aria-hidden="true" />
            Add product images
          </button>
        </div>
        <div className="admin-stats">
          <article>
            <span>Live products</span>
            <b>{products.length}</b>
          </article>
          <article>
            <span>Low stock</span>
            <b>{lowStock}</b>
          </article>
          <article>
            <span>Units tracked</span>
            <b>{totalStock}</b>
          </article>
          <article>
            <span>Inventory value</span>
            <b>{formatCurrency(inventoryValue)}</b>
          </article>
        </div>
        <div className="analysis-grid">
          <article className="chart-panel">
            <div>
              <BarChart3 aria-hidden="true" />
              <strong>Stock by product</strong>
            </div>
            {chartProducts.length > 0 ? (
              <div className="bar-chart" aria-label="Product stock chart">
                {chartProducts.map((product) => (
                  <span
                    key={product.id}
                    aria-label={`${product.name}: ${product.stock} units`}
                    style={{ height: `${Math.max((product.stock / maxStock) * 100, 8)}%` }}
                    title={`${product.name}: ${product.stock}`}
                  />
                ))}
              </div>
            ) : (
              <div className="chart-empty">No product stock data yet</div>
            )}
          </article>
          <article className="chart-panel">
            <div>
              <TrendingUp aria-hidden="true" />
              <strong>Analysis status</strong>
            </div>
            {products.length > 0 ? (
              <p>
                Showing live catalog totals. Order trend analysis should connect to order and
                inventory event APIs when those endpoints are available.
              </p>
            ) : (
              <div className="chart-empty">No analytics data until products or orders exist</div>
            )}
          </article>
        </div>
      </div>
    </section>
  );
}
