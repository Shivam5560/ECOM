import { useEffect, useState } from "react";

import { AdminConsole, FutureStockSpec } from "./components/admin/AdminConsole";
import { AdminDashboardSummary } from "./components/admin/AdminDashboardSummary";
import { AuthSheet } from "./components/auth/AuthSheet";
import { CartSheet } from "./components/cart/CartSheet";
import { CatalogScreen } from "./components/catalog/CatalogScreen";
import { Header, type ShopperScreen } from "./components/layout/Header";
import { OrdersScreen } from "./components/orders/OrdersScreen";
import { SupportScreen } from "./components/support/SupportScreen";
import { listOrders, type Order } from "./lib/api/orders";
import {
  initProducts,
  listProducts,
  type ResourceInit,
} from "./lib/api/products";
import { sessionFromAuth, type Session } from "./lib/session";
import type { Product } from "./types";

export default function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [productInit, setProductInit] = useState<ResourceInit | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [status, setStatus] = useState("Loading product init links from gateway...");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [session, setSession] = useState<Session | null>(null);
  const [activeScreen, setActiveScreen] = useState<ShopperScreen>("catalog");
  const [isSignInOpen, setIsSignInOpen] = useState(false);

  async function loadProducts() {
    const init = await initProducts();
    const page = await listProducts({ path: init.links.list });
    setProductInit(init);
    setProducts(page.items);
    setStatus(`Loaded ${page.total} products from ${init.links.list}`);
  }

  async function loadOrders(currentSession: Session | null) {
    if (!currentSession) {
      setOrders([]);
      return;
    }
    const page = await listOrders({ token: currentSession.accessToken });
    setOrders(page.items);
  }

  useEffect(() => {
    loadProducts().catch(() => {
      setStatus("Gateway product API unavailable");
    });
  }, []);

  useEffect(() => {
    loadOrders(session).catch(() => setOrders([]));
  }, [session]);

  return (
    <>
      <Header
        activeScreen={activeScreen}
        session={session}
        onScreenChange={setActiveScreen}
        onSignIn={() => setIsSignInOpen(true)}
        onSignOut={() => {
          setSession(null);
          setOrders([]);
        }}
      />
      {session?.role === "admin" ? (
        <main>
          <AdminDashboardSummary products={products} />
          <AdminConsole
            init={productInit}
            products={products}
            selectedIds={selectedIds}
            setSelectedIds={setSelectedIds}
            onRefresh={loadProducts}
            setStatus={setStatus}
            session={session}
          />
          <FutureStockSpec />
        </main>
      ) : (
        <main>
          {activeScreen === "catalog" ? <CatalogScreen products={products} status={status} /> : null}
          {activeScreen === "orders" ? (
            <OrdersScreen
              orders={orders}
              session={session}
              onRequireSignIn={() => setIsSignInOpen(true)}
            />
          ) : null}
          {activeScreen === "support" ? <SupportScreen /> : null}
        </main>
      )}
      {session?.role !== "admin" ? (
        <CartSheet session={session} onRequireSignIn={() => setIsSignInOpen(true)} />
      ) : null}
      <AuthSheet
        isOpen={isSignInOpen}
        onClose={() => setIsSignInOpen(false)}
        onSignIn={(authSession) => setSession(sessionFromAuth(authSession))}
      />
    </>
  );
}
