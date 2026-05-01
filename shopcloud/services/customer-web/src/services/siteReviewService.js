import { changeSiteReview, changeSiteReviewStatus, createSiteReview, deleteSiteReviewApi, getSiteReviews, getUserSiteReviews } from "../api/siteReviewApi";



export async function submitSiteReview(rating, comment) {
    const response = await createSiteReview(rating, comment);
    return response.data;
}

export async function fetchSiteReviews() {
    const response = await getSiteReviews();
    return response.data.reviews;
}

export async function fetchUserSiteReviews() {
    const response = await getUserSiteReviews();
    return response.data.reviews;
}

export async function updateSiteReview(reviewId, rating, comment) {
    const response = await changeSiteReview(reviewId, rating, comment);
    return response.data;
}

export async function updateSiteReviewStatus(reviewId, isApproved) {
    const response = await changeSiteReviewStatus(reviewId, isApproved);
    return response.data;
}

export async function deleteSiteReview(reviewId) {
    const response = await deleteSiteReviewApi(reviewId);
    return response.data.message;
}