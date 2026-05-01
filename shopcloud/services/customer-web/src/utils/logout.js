import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

export default function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const logout = () => {
    // Remove auth data
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("user");

    // Clear all cached queries
    queryClient.clear();

    // Show toast
    toast.success("Logged out successfully");

    // Redirect
    navigate("/login");
  };

  return logout;
}
