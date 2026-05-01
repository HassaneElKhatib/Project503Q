import { useQuery } from "@tanstack/react-query";
import { fetchClientDashboardOverview } from "../services/dashboardService";


export function useClientDashboard(userId, options = {}) {
  return useQuery({
    queryKey: ["dashboard", "client", userId],
    queryFn: async () => {
      const response = await fetchClientDashboardOverview();
      return response;
    },
    enabled: options.enabled ?? Boolean(userId),
    staleTime: 1000 * 60 * 10, // 10 minutes
    onError: (error) => {
      console.error("Failed to fetch client dashboard data:", error);
    }
  });
}