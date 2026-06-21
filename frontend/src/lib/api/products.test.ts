import { describe, expect, it, vi } from "vitest";

import { bulkDeleteProducts, initProducts, listProducts } from "./products";

describe("product api", () => {
  it("loads product init and list links through the gateway", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            resource: "products",
            links: { list: "/api/v1/products", bulk_delete: "/api/v1/products" },
            actions: {},
            bulkActions: ["bulk_delete"],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ items: [], total: 0, page: 1, size: 20, pages: 0 }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

    const init = await initProducts({ baseUrl: "http://gateway.test", fetcher });
    await listProducts({ baseUrl: "http://gateway.test", fetcher, path: init.links.list });

    expect(fetcher).toHaveBeenNthCalledWith(1, "http://gateway.test/api/v1/products/init", undefined);
    expect(fetcher).toHaveBeenNthCalledWith(2, "http://gateway.test/api/v1/products", undefined);
  });

  it("bulk deletes product ids through discovered gateway link", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ deleted: ["p-1"], missing: ["p-2"] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const result = await bulkDeleteProducts({
      ids: ["p-1", "p-2"],
      path: "/api/v1/products",
      options: { baseUrl: "http://gateway.test", fetcher, token: "admin-token" },
    });

    expect(fetcher).toHaveBeenCalledWith("http://gateway.test/api/v1/products", {
      method: "DELETE",
      headers: { "Content-Type": "application/json", Authorization: "Bearer admin-token" },
      body: JSON.stringify({ ids: ["p-1", "p-2"] }),
    });
    expect(result.deleted).toEqual(["p-1"]);
  });
});
