import api from "../config/axiosConfig";

// Create a review
export function reviewApi(productId, rating, comment) {
  return api.post("/reviews", { productId, rating, comment });
}

// Get reviews for a specific product
export function getProductReviewsApi(productId) {
  return api.get(`/reviews/product/${productId}`);
}

// Get reviews by the logged-in user
export function getUserReviewsApi() {
  return api.get("/reviews/user");
}

export function getAllReviewsApi() {
  return api.get("/reviews");
}

// Update a review
export function updateReviewApi(reviewId, rating, comment) {
  return api.put(`/reviews/${reviewId}`, { rating, comment });
}

// Delete a review
export function deleteReviewApi(reviewId) {
  return api.delete(`/reviews/${reviewId}`);
}
