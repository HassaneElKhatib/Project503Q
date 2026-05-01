import toast from "react-hot-toast";
import { fetchUserDetails, updateUserDetails } from "../api/userApi";

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

// Fetch user details
export async function getUserById() {
  try{
    const response = await fetchUserDetails();
    const userPayload = response.data?.user ?? response.data ?? null;
    return normalizeUser(userPayload);

  }catch(err) {
    console.log("Faild to fetch user details:", err);
    return null;
  }
}

// Update user details
export async function updateUserById(updatedUserData) {
  try{
    const payload = { ...updatedUserData };
    if (!payload.name && (payload.firstName || payload.lastName)) {
      payload.name = `${payload.firstName || ""} ${payload.lastName || ""}`.trim();
    }
    if (payload.newPassword) {
      payload.password = payload.newPassword;
    }
    const response = await updateUserDetails(payload);
    toast.success(response.data?.message || "User details updated successfully!");
    const userPayload = response.data?.user ?? response.data ?? null;
    return normalizeUser(userPayload);
  }catch(err) {
    console.log("Failed to update user details:", err);
    toast.error(err.response?.data?.message || "Failed to update user details.");
    return null;
  }
}