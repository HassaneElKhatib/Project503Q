import api from "../config/axiosConfig"


// Normal login
export const loginUser = (data, path = "/login") => {
  return api.post("/users" + path, data);
}

// Google login
export const googleLoginUser = (googleToken) => {
  return api.post("/users/google-login", { googleToken });
}

// Register new user
export const registerUser = (userData) => {
  return api.post("/users", userData );
}

// Fetch user details
export const fetchUserDetails = () => {
  return api.get("/users/me/");
}

export const fetchAdminDetails = () => {
  return api.get("/users/me/admin");
}

// Update user details
export const updateUserDetails = (updatedUserData) => {
  return api.put("/users/", updatedUserData);
}
