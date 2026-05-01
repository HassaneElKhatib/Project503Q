import api from "../config/axiosConfig";

// Create a site review
export function createSiteReview(rating, comment) {
  return api.post("/site-reviews", { rating, comment });
}

// Get all site reviews
export function getSiteReviews() {
  return api.get("/site-reviews");
}

// Get user-specific site reviews
export function getUserSiteReviews() {
  return api.get("/site-reviews/user");
}

// Update a site review
export function changeSiteReview(reviewId, rating, comment) {
  return api.put(`/site-reviews/${reviewId}`, { rating, comment });
}

// Update site review status (admin)
export function changeSiteReviewStatus(reviewId, isApproved) {
  return api.put(`/site-reviews/status/${reviewId}`, { isApproved });
}

// Delete a site review
export function deleteSiteReviewApi(reviewId) {
  return api.delete(`/site-reviews/${reviewId}`);
}