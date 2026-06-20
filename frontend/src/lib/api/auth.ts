import { postJson, type ApiOptions } from "./client";

const defaultAuthUrl = import.meta.env.VITE_AUTH_API_URL ?? "";

export type AuthCredentials = {
  email: string;
  password: string;
};

type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type AuthSession = {
  accessToken: string;
  tokenType: string;
};

function normalizeToken(response: TokenResponse): AuthSession {
  return {
    accessToken: response.access_token,
    tokenType: response.token_type,
  };
}

export async function login(
  credentials: AuthCredentials,
  options: ApiOptions = {},
): Promise<AuthSession> {
  const response = await postJson<TokenResponse, AuthCredentials>(
    "/auth/login",
    credentials,
    { baseUrl: options.baseUrl ?? defaultAuthUrl, fetcher: options.fetcher },
  );
  return normalizeToken(response);
}

export async function register(
  credentials: AuthCredentials,
  options: ApiOptions = {},
): Promise<AuthSession> {
  const response = await postJson<TokenResponse, AuthCredentials>(
    "/auth/register",
    credentials,
    { baseUrl: options.baseUrl ?? defaultAuthUrl, fetcher: options.fetcher },
  );
  return normalizeToken(response);
}
