import { LogOut, ShoppingBag, UserRound } from "lucide-react";

import { Button } from "../ui/Button";
import { useCartStore } from "../../store/cart";
import type { Session } from "../../lib/session";

export type ShopperScreen = "catalog" | "orders" | "support";

type HeaderProps = {
  session: Session | null;
  activeScreen: ShopperScreen;
  onScreenChange: (screen: ShopperScreen) => void;
  onSignIn: () => void;
  onSignOut: () => void;
};

export function Header({ session, activeScreen, onScreenChange, onSignIn, onSignOut }: HeaderProps) {
  const itemCount = useCartStore((state) => state.itemCount());
  const openCart = useCartStore((state) => state.openCart);
  const isAdmin = session?.role === "admin";

  return (
    <header className="site-header">
      <a
        className="brand"
        href="#catalog"
        aria-label="ECOM home"
        onClick={() => onScreenChange("catalog")}
      >
        <span>ECOM</span>
      </a>
      <nav className="main-nav" aria-label="Primary navigation">
        {isAdmin ? (
          <>
            <a href="#dashboard">Dashboard</a>
            <a href="#admin">Products</a>
            <a href="#future-stock">Stock spec</a>
          </>
        ) : (
          <>
            {(["catalog", "orders", "support"] as const).map((screen) => (
              <a
                href={`#${screen}`}
                key={screen}
                className={activeScreen === screen ? "active" : ""}
                onClick={(event) => {
                  event.preventDefault();
                  onScreenChange(screen);
                }}
              >
                {screen}
              </a>
            ))}
          </>
        )}
      </nav>
      <div className="header-actions">
        {session ? (
          <Button variant="ghost" onClick={onSignOut}>
            <LogOut data-icon="inline-start" aria-hidden="true" />
            Sign out
          </Button>
        ) : (
          <Button variant="ghost" onClick={onSignIn}>
            <UserRound data-icon="inline-start" aria-hidden="true" />
            Sign in
          </Button>
        )}
        {!isAdmin ? (
          <Button className="cart-button" variant="primary" onClick={openCart}>
            <ShoppingBag data-icon="inline-start" aria-hidden="true" />
            Cart
            <strong>{itemCount}</strong>
          </Button>
        ) : null}
      </div>
    </header>
  );
}
