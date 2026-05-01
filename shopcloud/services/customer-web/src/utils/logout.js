import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useHostedCognitoAuth } from "./authMode";
import { publicApiOrigin } from "./publicApiOrigin";

export default function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const cognitoHosted = useHostedCognitoAuth();

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("user");

    queryClient.clear();

    toast.success("Logged out successfully");

    if (cognitoHosted) {
      const base = publicApiOrigin();
      const isAdmin = window.location.pathname.startsWith("/admin");
      const action = isAdmin ? `${base}/auth/admin/logout` : `${base}/auth/logout`;
      const f = document.createElement("form");
      f.method = "POST";
      f.action = action;
      document.body.appendChild(f);
      f.submit();
      return;
    }

    navigate("/login");
  };

  return logout;
}
