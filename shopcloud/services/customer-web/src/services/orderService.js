import { fetchOrders } from "../api/ordersApi";


export async function getOrders(page, limit) {
  const response = await fetchOrders(page,limit);
  return response.data;
}