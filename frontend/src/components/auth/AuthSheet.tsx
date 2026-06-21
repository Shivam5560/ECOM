import { LockKeyhole } from "lucide-react";
import { useState } from "react";

import { login, register, type AuthSession } from "../../lib/api/auth";
import { Button } from "../ui/Button";
import { Sheet } from "../ui/Sheet";

type AuthSheetProps = {
  isOpen: boolean;
  onClose: () => void;
  onSignIn: (session: AuthSession) => void;
};

export function AuthSheet({ isOpen, onClose, onSignIn }: AuthSheetProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("Calls the gateway auth endpoints for sign in and account creation.");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(mode: "login" | "register") {
    if (!email.trim() || !password.trim()) {
      setStatus("Email and password are required");
      return;
    }

    setIsSubmitting(true);
    setStatus(mode === "login" ? "Signing in through gateway..." : "Creating account through gateway...");
    try {
      const session = mode === "login"
        ? await login({ email, password })
        : await register({ email, password });
      onSignIn(session);
      onClose();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : mode === "login" ? "Sign in failed" : "Registration failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Sheet className="signin-dialog" eyebrow="Gateway auth" isOpen={isOpen} onClose={onClose} title="Gateway sign in">
      <div className="sheet-callout">
        <LockKeyhole aria-hidden="true" />
        <span>Requests go to the configured gateway URL, not auth-service or user-service directly.</span>
      </div>
      <label>
        Email
        <input value={email} onChange={(event) => setEmail(event.target.value)} />
      </label>
      <label>
        Password
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </label>
      <Button fullWidth variant="primary" disabled={isSubmitting} onClick={() => submit("login")}>
        Sign in
      </Button>
      <Button fullWidth variant="secondary" disabled={isSubmitting} onClick={() => submit("register")}>
        Create account
      </Button>
      <p className="checkout-status" aria-live="polite">
        {status}
      </p>
    </Sheet>
  );
}
