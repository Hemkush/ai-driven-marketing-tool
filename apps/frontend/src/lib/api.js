import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

export const api = axios.create({
  baseURL: API_BASE,
});

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    localStorage.setItem("access_token", token);
  } else {
    delete api.defaults.headers.common.Authorization;
    localStorage.removeItem("access_token");
  }
}

export function initAuthToken() {
  const token = localStorage.getItem("access_token");
  if (token) {
    setAuthToken(token);
  }
  return token;
}

// Auto-clear expired/invalid tokens and redirect to login.
// Skip the redirect for the login endpoint itself — a 401 there just means wrong credentials.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthEndpoint = error.config?.url?.includes("/auth/login") ||
                           error.config?.url?.includes("/auth/register");
    if (error.response?.status === 401 && !isAuthEndpoint) {
      setAuthToken(null);
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);
