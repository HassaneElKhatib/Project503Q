import toast from "react-hot-toast";
import  { fetchDashboardData, fetchClientDashboardData } from "../api/dashboardApi";


export async function fetchDashboardOverview() {
  try {
    const response = await fetchDashboardData();
    console.log("Dashboard data fetched:", response);
    return response;
  } catch (error) {
    toast.error("Failed to fetch dashboard data");
    console.error("Error fetching dashboard data:", error);
    throw error;
  }
}


export async function fetchClientDashboardOverview() {
  try {
    const response = await fetchClientDashboardData();
    return response;
  } catch (error) {
    toast.error("Failed to fetch client dashboard data");
    console.error("Error fetching client dashboard data:", error);
    throw error;
  }
}