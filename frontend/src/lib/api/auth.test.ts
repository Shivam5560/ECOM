import { describe, expect, it, vi } from "vitest";

import { login, register } from "./auth";

describe("auth api", () => {
  it("posts login credentials to the auth service", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ access_token: "token-1", token_type: "bearer" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const result = await login(
      { email: "buyer@ecom.dev", password: "secret" },
      { baseUrl: "http://auth.test", fetcher },
    );

    expect(fetcher).toHaveBeenCalledWith("http://auth.test/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "buyer@ecom.dev", password: "secret" }),
    });
    expect(result.accessToken).toBe("token-1");
  });

  it("throws a readable error when registration fails", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "email already exists" }), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(
      register(
        { email: "buyer@ecom.dev", password: "secret" },
        { baseUrl: "http://auth.test", fetcher },
      ),
    ).rejects.toThrow("email already exists");
  });
});
