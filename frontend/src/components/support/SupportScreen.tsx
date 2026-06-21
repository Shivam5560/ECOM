import { Mail, MessageCircle, ShieldCheck } from "lucide-react";

export function SupportScreen() {
  return (
    <section className="support-screen" id="support">
      <div className="section-heading">
        <div>
          <h1>Support</h1>
          <p>
            Gateway-backed help for catalog questions, checkout issues, and order follow-up without
            exposing internal service links.
          </p>
        </div>
        <ShieldCheck aria-hidden="true" />
      </div>
      <div className="support-grid">
        <article>
          <MessageCircle aria-hidden="true" />
          <h2>Checkout help</h2>
          <p>Get help with cart quantity, COD selection, or order placement problems.</p>
        </article>
        <article>
          <Mail aria-hidden="true" />
          <h2>Order follow-up</h2>
          <p>Use your order ID and email to coordinate support through gateway workflows.</p>
        </article>
        <article>
          <ShieldCheck aria-hidden="true" />
          <h2>Account access</h2>
          <p>Sign in or create an account using gateway auth endpoints from the secure sheet.</p>
        </article>
      </div>
    </section>
  );
}
