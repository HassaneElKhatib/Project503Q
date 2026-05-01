import api from "../config/axiosConfig";


export async function fetchDashboardData() {
  try {
    const response = await api.get("/dashboard");
    return response.data;
  } catch (error) {
    console.error("Failed to fetch dashboard data", error);
    throw error;
  }
}

export async function fetchClientDashboardData() {
  try {
    const response = await api.get("/dashboard/client");
    return response.data;
  } catch (error) {
    console.error("Failed to fetch client dashboard data", error);
    throw error;
  }
}