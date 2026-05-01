import api from "../config/axiosConfig"


export const fetchOrders = (page, limit) => {
  return api.get(`/orders/history/${page}/${limit}`);
}