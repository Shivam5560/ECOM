import type { AuthSession } from "./api/auth";

export type SessionRole = "user" | "admin" | null;

export type Session = {
  accessToken: string;
  role: Exclude<SessionRole, null>;
  email?: string;
};

export function sessionFromAuth(auth: AuthSession): Session {
  const [, encodedPayload] = auth.accessToken.split(".");
  let roles: string[] = [];
  let email: string | undefined;

  if (encodedPayload) {
    try {
      const normalized = encodedPayload.replaceAll("-", "+").replaceAll("_", "/");
      const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
      const payload = JSON.parse(atob(padded));
      roles = Array.isArray(payload.roles) ? payload.roles : [];
      email = typeof payload.email === "string" ? payload.email : undefined;
    } catch {
      roles = [];
    }
  }

  return {
    accessToken: auth.accessToken,
    role: roles.includes("admin") ? "admin" : "user",
    email,
  };
}
