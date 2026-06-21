export type ApiOptions = {
  baseUrl?: string;
  fetcher?: typeof fetch;
  token?: string;
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
    headers: jsonHeaders(options),
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
  const response = await fetcher(`${baseUrl}${path}`, undefined);
  const body = (await response.json().catch(() => ({}))) as BackendError;

  if (!response.ok) {
    throw new Error(
      body.detail ?? body.error?.message ?? body.message ?? "Request failed",
    );
  }

  return body as TResponse;
}

export async function patchJson<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  options: ApiOptions = {},
): Promise<TResponse> {
  const baseUrl = options.baseUrl ?? "";
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(`${baseUrl}${path}`, {
    method: "PATCH",
    headers: jsonHeaders(options),
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

export async function deleteJson<TResponse, TPayload = undefined>(
  path: string,
  payload?: TPayload,
  options: ApiOptions = {},
): Promise<TResponse> {
  const baseUrl = options.baseUrl ?? "";
  const fetcher = options.fetcher ?? fetch;
  const init: RequestInit = {
    method: "DELETE",
    headers: jsonHeaders(options),
  };
  if (payload !== undefined) {
    init.body = JSON.stringify(payload);
  }
  const response = await fetcher(`${baseUrl}${path}`, init);
  const body = (await response.json().catch(() => ({}))) as BackendError;

  if (!response.ok) {
    throw new Error(
      body.detail ?? body.error?.message ?? body.message ?? "Request failed",
    );
  }

  return body as TResponse;
}

function jsonHeaders(options: ApiOptions): HeadersInit {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  return headers;
}
