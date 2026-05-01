import axios from "axios";
import { publicApiBase } from "../utils/publicApiOrigin";

export function optionalBearerHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const api = axios.create({
  baseURL: publicApiBase(),
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const extra = optionalBearerHeaders();
  if (extra.Authorization) {
    config.headers.Authorization = extra.Authorization;
  }
  return config;
});

export default api;
