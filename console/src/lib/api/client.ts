import type { ApiError } from "./types";

export class ConsoleApiError extends Error implements ApiError {
  status: number;
  endpoint: string;

  constructor(status: number, message: string, endpoint: string) {
    super(message);
    this.name = "ConsoleApiError";
    this.status = status;
    this.endpoint = endpoint;
  }
}

export async function fetchJson<T>(
  url: string,
  options: RequestInit & { timeoutMs?: number } = {}
): Promise<T> {
  const { timeoutMs = 8000, ...fetchOptions } = options;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...fetchOptions.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let message = response.statusText || "Request failed";
      try {
        const errorJson = await response.json();
        if (errorJson?.message) {
          message = errorJson.message;
        } else if (errorJson?.error) {
          message = errorJson.error;
        }
      } catch {
        // use response status text if body not json
      }
      throw new ConsoleApiError(response.status, message, url);
    }

    const data = await response.json();
    return data as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof ConsoleApiError) {
      throw err;
    }
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ConsoleApiError(0, "Request timeout", url);
    }
    const message = err instanceof Error ? err.message : "Network error";
    throw new ConsoleApiError(0, message, url);
  }
}
