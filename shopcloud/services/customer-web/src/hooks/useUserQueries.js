import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchUserDetails, updateUserDetails } from "../api/userApi";
import toast from "react-hot-toast";

function normalizeUser(user) {
  if (!user) return null;
  const name = user.name || [user.firstName, user.lastName].filter(Boolean).join(" ").trim();
  const [firstName = "", ...rest] = (name || "").split(" ");
  return {
    ...user,
    name,
    firstName: user.firstName || firstName,
    lastName: user.lastName || rest.join(" "),
  };
}


// Query Keys 
export const USER_KEYS = {
  user: ["user"],
  userById: (id) => ["user",id]
};

// Fetch current user details
// This will cache the data and share it across all components using this hook
export function useUser() {
  return useQuery({
    queryKey: USER_KEYS.user,
    queryFn: async () => {
      const response = await fetchUserDetails();
      const userPayload = response.data?.user ?? response.data ?? null;
      return normalizeUser(userPayload);
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
    onError: (error) => {
      console.error("Failed to fetch user details:", error);
    }
  })
}

// Update user details
// This will automatically invalidate the cache and refetch data
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updatedUserData) => {
      const payload = { ...updatedUserData };
      if (!payload.name && (payload.firstName || payload.lastName)) {
        payload.name = `${payload.firstName || ""} ${payload.lastName || ""}`.trim();
      }
      if (payload.newPassword) {
        payload.password = payload.newPassword;
      }
      const response = await updateUserDetails(payload);
      return normalizeUser(response.data?.user ?? response.data ?? null);
    },
    onSuccess: () => {
      // Invalidate and refetch user query after successful update
      queryClient.invalidateQueries({queryKey: USER_KEYS.user});
      toast.success("User details updated successfully");
    },
    onError: (error) => {
      console.error("Failed to update user details:", error);
      toast.error(error.response?.data?.message || "Failed to update user details");
    }
  });
}

// Update password
export function useUpdatePassword() {
  return useMutation({
    mutationFn: async ({ currentPassword, newPassword }) => {
      const response = await updateUserDetails({ currentPassword, newPassword });
      return response.data;
    },
    onSuccess: () => {
      toast.success("Password Updated Sucessfully");
    },
    onError: (error) => {
      console.error("Failed to update password:", error);
      toast.error(error.response?.data?.message || "Failed to update password.");
    }
  });
}