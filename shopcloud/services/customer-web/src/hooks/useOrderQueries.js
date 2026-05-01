import { useQuery } from "@tanstack/react-query"
import { fetchOrders } from "../api/ordersApi"


export const ORDER_KEYS = {
  orders: (page, limit) => ["orders", page, limit] //Different key for each page/limit combination
}

export function useOrders(page, limit) {
  return useQuery({
    queryKey: ORDER_KEYS.orders(page, limit),
    queryFn: async () => {
      const response = await fetchOrders(page, limit);
      return response.data;
    },
    onError: (error) => {
      console.error("Failed to fetch orders:", error);
    }
  })
}

