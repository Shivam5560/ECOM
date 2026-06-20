export type ApiOptions = {
  baseUrl?: string;
  fetcher?: typeof fetch;
};

type BackendError = {
  detail?: string;
  message?: string;
  error?: { message?: string };
};

export async function postJson<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  options: ApiOptions = {},
): Promise<TResponse> {
  const baseUrl = options.baseUrl ?? "";
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const body = (await response.json().catch(() => ({}))) as BackendError;

  if (!response.ok) {
    throw new Error(
      body.detail ?? body.error?.message ?? body.message ?? "Request failed",
    );
  }

  return body as TResponse;
}

export async function getJson<TResponse>(
  path: string,
  options: ApiOptions = {},
): Promise<TResponse> {
  const baseUrl = options.baseUrl ?? "";
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(`${baseUrl}${path}`);
  const body = (await response.json().catch(() => ({}))) as BackendError;

  if (!response.ok) {
    throw new Error(
      body.detail ?? body.error?.message ?? body.message ?? "Request failed",
    );
  }

  return body as TResponse;
}
