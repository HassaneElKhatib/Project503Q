import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteSiteReview,
  fetchSiteReviews,
  fetchUserSiteReviews,
  submitSiteReview,
  updateSiteReview,
  updateSiteReviewStatus
} from "../services/siteReviewService";
import toast from "react-hot-toast";

export const SITE_REVIEW_KEYS = {
  all: ["siteReviews"],
  user: ["userSiteReviews"],
};

// Hook to create a new site review
export function useCreateSiteReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ rating, comment }) =>
      submitSiteReview(rating, comment),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SITE_REVIEW_KEYS.all });
      queryClient.invalidateQueries({ queryKey: SITE_REVIEW_KEYS.user });
      toast.success("Thank you for your review!");
    },

    onError: (error) => {
      console.error("Failed to submit review", error);
      toast.error(error.response?.data?.message || "Failed to submit review");
    }
  });
}

// Hook to fetch all site reviews
export function useSiteReviewQueries() {
  return useQuery({
    queryKey: SITE_REVIEW_KEYS.all,

    queryFn: fetchSiteReviews,

    staleTime: 1000 * 60 * 15, // 15 minutes

    onError: (error) => {
      console.error("Failed to fetch site reviews:", error);
    }
  });
}

// Hook to fetch site reviews submitted by the user
export function useUserSiteReviewQueries() {
  return useQuery({
    queryKey: SITE_REVIEW_KEYS.user,

    queryFn: fetchUserSiteReviews,

    onError: (error) => {
      console.error("Failed to fetch user site reviews:", error);
      toast.error(
        error.response?.data?.message || "Failed to fetch user site reviews"
      );
    }
  });
}

// Hook to update an existing site review
export function useUpdateSiteReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reviewId, rating, comment }) =>
      updateSiteReview(reviewId, rating, comment),

    onSuccess: () => {
      // refetch site reviews after successful update
      queryClient.invalidateQueries({ queryKey: SITE_REVIEW_KEYS.all });
      queryClient.invalidateQueries({ queryKey: SITE_REVIEW_KEYS.user });
      toast.success("Review updated successfully!");
    },

    onError: (error) => {
      console.error("Failed to update review:", error);
      toast.error(error.response?.data?.message || "Failed to update review.");
    }
  });
}

// Hook to update the status of a site review 
export function useUpdateSiteReviewStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reviewId, status }) =>
      updateSiteReviewStatus(reviewId, status),

    onSuccess: () => {
      // refetch site reviews after successful status update
      queryClient.invalidateQueries({ queryKey: SITE_REVIEW_KEYS.all });
      toast.success("Review status updated successfully!");
    },

    onError: (error) => {
      console.error("Failed to update review status:", error);
      toast.error(
        error.response?.data?.message || "Failed to update review status."
      );
    }
  });
}

// Hook to delete a site review
export function useDeleteSiteReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewId) =>
      deleteSiteReview(reviewId),

    onSuccess: () => {
      // refetch site reviews after successful deletion
      queryClient.invalidateQueries({ queryKey: SITE_REVIEW_KEYS.all });
      queryClient.invalidateQueries({ queryKey: SITE_REVIEW_KEYS.user });
      toast.success("Review deleted successfully!");
    },

    onError: (error) => {
      console.error("Failed to delete review:", error);
      toast.error(error.response?.data?.message || "Failed to delete review.");
    }
  });
}
