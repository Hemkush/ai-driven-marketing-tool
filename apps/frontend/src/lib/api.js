import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/api";

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
