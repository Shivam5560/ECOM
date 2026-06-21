import { Edit3, Layers, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  bulkDeleteProducts,
  createProducts,
  updateProduct,
  type ResourceInit,
} from "../../lib/api/products";
import { formatCurrency } from "../../lib/format";
import type { Session } from "../../lib/session";
import type { Product } from "../../types";

type AdminForm = {
  name: string;
  category: string;
  description: string;
  price: string;
  stock: string;
  image: string;
  rating: string;
  accent: string;
};

const starterForm: AdminForm = {
  name: "",
  category: "",
  description: "",
  price: "",
  stock: "",
  image: "",
  rating: "",
  accent: "#d7ff38",
};

type AdminConsoleProps = {
  init: ResourceInit | null;
  products: Product[];
  selectedIds: string[];
  setSelectedIds: (ids: string[]) => void;
  onRefresh: () => Promise<void>;
  setStatus: (status: string) => void;
  session: Session;
};

export function AdminConsole({
  init,
  products,
  selectedIds,
  setSelectedIds,
  onRefresh,
  setStatus,
  session,
}: AdminConsoleProps) {
  const [form, setForm] = useState(starterForm);
  const [editId, setEditId] = useState(products[0]?.id ?? "");

  async function addProduct() {
    if (!init) {
      setStatus("Product init links are required before registering products");
      return;
    }
    if (!form.name.trim() || !form.category.trim() || !form.price.trim() || !form.stock.trim() || !form.image.trim()) {
      setStatus("Name, category, price, stock, and image URL are required");
      return;
    }
    await createProducts({
      path: init.links.create,
      payload: {
        id: form.name.trim().toLowerCase().replaceAll(" ", "-"),
        name: form.name,
        category: form.category,
        description: form.description,
        price: Number(form.price),
        stock: Number(form.stock),
        rating: Number(form.rating || 0),
        image: form.image,
        accent: form.accent || "#d7ff38",
      },
      options: { token: session.accessToken },
    });
    setStatus("Product registered through gateway link");
    await onRefresh();
  }

  async function updateSelected() {
    if (!init || !editId) {
      setStatus("Choose a product before update");
      return;
    }
    await updateProduct({
      id: editId,
      path: init.actions.update ?? "/api/v1/products/{id}",
      payload: {
        price: Number(form.price),
        stock: Number(form.stock),
        description: form.description,
      },
      options: { token: session.accessToken },
    });
    setStatus(`Updated ${editId} through gateway link`);
    await onRefresh();
  }

  async function deleteSelected() {
    if (!init || selectedIds.length === 0) {
      setStatus("Select products before bulk delete");
      return;
    }
    const result = await bulkDeleteProducts({
      ids: selectedIds,
      path: init.links.bulk_delete,
      options: { token: session.accessToken },
    });
    setStatus(`Deleted ${result.deleted.length}; missing ${result.missing.length}`);
    setSelectedIds([]);
    await onRefresh();
  }

  return (
    <section className="admin-console" id="admin">
      <div className="admin-hero">
        <div>
          <p>Admin workspace</p>
          <h2>Admin catalog console</h2>
        </div>
        <div className="link-strip">
          <span>Init</span>
          <strong>{init?.links.list ?? "loading"}</strong>
        </div>
      </div>
      <div className="admin-layout">
        <div className="admin-form">
          {(["name", "category", "description", "price", "stock", "image", "rating", "accent"] as const).map((key) => (
            <label key={key}>
              {key === "image" ? "image URL" : key}
              <input
                value={form[key]}
                onChange={(event) => setForm({ ...form, [key]: event.target.value })}
              />
            </label>
          ))}
          <label>
            update target
            <select value={editId} onChange={(event) => setEditId(event.target.value)}>
              <option value="">Select product</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </select>
          </label>
          <div className="admin-actions">
            <button type="button" onClick={addProduct}>
              <Plus aria-hidden="true" />
              <span>Add</span>
            </button>
            <button type="button" onClick={updateSelected}>
              <Edit3 aria-hidden="true" />
              <span>Update</span>
            </button>
            <button className="danger-action" type="button" onClick={deleteSelected}>
              <Trash2 aria-hidden="true" />
              <span>Bulk delete</span>
            </button>
          </div>
        </div>
        <div className="operations-table" role="table" aria-label="Admin product operations">
          <div className="ops-row ops-head" role="row">
            <span role="columnheader">Select</span>
            <span role="columnheader">Product</span>
            <span role="columnheader">Category</span>
            <span role="columnheader">Price</span>
            <span role="columnheader">Stock</span>
          </div>
          {products.map((row) => (
            <div className="ops-row" role="row" key={row.id}>
              <label className="check-cell">
                <input
                  type="checkbox"
                  checked={selectedIds.includes(row.id)}
                  onChange={(event) =>
                    setSelectedIds(
                      event.target.checked
                        ? [...selectedIds, row.id]
                        : selectedIds.filter((id) => id !== row.id),
                    )
                  }
                />
                <span className="sr-only">Select {row.name}</span>
              </label>
              <span role="cell">{row.name}</span>
              <span role="cell">{row.category}</span>
              <span role="cell">{formatCurrency(row.price)}</span>
              <span role="cell">{row.stock}</span>
            </div>
          ))}
          {products.length === 0 ? (
            <div className="ops-empty" role="row">
              <span role="cell">No products returned from the product API yet.</span>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

export function FutureStockSpec() {
  return (
    <section className="future-stock" id="future-stock">
      <div>
        <Layers aria-hidden="true" />
        <h2>Stock and image entry spec</h2>
      </div>
      <p>
        Current admin actions can add/update/delete product basics through the gateway. The next
        implementation should add per-product stock intake, warehouse adjustments, main image,
        gallery images, variant images, collection hero image, alt text, focal point, and sort order.
      </p>
    </section>
  );
}
