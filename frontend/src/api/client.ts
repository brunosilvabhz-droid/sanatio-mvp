import axios from 'axios';

function resolveApiBaseUrl() {
  const configuredUrl = import.meta.env.VITE_API_URL;
  const browserHost = window.location.hostname;
  const isBrowserLocalhost = browserHost === 'localhost' || browserHost === '127.0.0.1';

  if (configuredUrl) {
    const configured = new URL(configuredUrl);
    const configuredIsLocalhost = configured.hostname === 'localhost' || configured.hostname === '127.0.0.1';
    if (!configuredIsLocalhost || isBrowserLocalhost) return configuredUrl;
  }

  return `${window.location.protocol}//${browserHost}:8000`;
}

export const api = axios.create({
  baseURL: resolveApiBaseUrl()
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sanatio_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sanatio_token');
      if (location.pathname !== '/login') location.href = '/login';
    }
    return Promise.reject(error);
  }
);
