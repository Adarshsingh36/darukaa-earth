import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MAX_RETRIES = 2;
const RETRY_DELAYS = [2000, 4000];

type RetryConfig = InternalAxiosRequestConfig & {
  __retryCount?: number;
};

export const api = axios.create({
  baseURL: API_URL,
  timeout: 20000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('darukaa_token');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail?: string | { msg: string }[] }>) => {
    const config = error.config as RetryConfig | undefined;

    const isNetworkError =
      error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT';

    const isServerError = error.response?.status !== undefined && error.response.status >= 500;

    const shouldRetry =
      config && (isNetworkError || isServerError) && (config.__retryCount ?? 0) < MAX_RETRIES;

    if (shouldRetry) {
      config.__retryCount = (config.__retryCount ?? 0) + 1;

      const retryIndex = config.__retryCount - 1;
      const delay = RETRY_DELAYS[retryIndex] ?? 4000;

      await new Promise((resolve) => setTimeout(resolve, delay));

      return api(config);
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('darukaa_token');
      localStorage.removeItem('darukaa_user');

      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  },
);

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg).join(', ');
    }

    if (
      error.code === 'ERR_NETWORK' ||
      error.code === 'ECONNABORTED' ||
      error.code === 'ETIMEDOUT'
    ) {
      return 'The server is waking up or temporarily unavailable. Please try again in a moment.';
    }

    return error.message || 'Something went wrong.';
  }

  return 'Something went wrong.';
}
