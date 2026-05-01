import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteReview,
  fetchUserReviews,
  submitReview,
  updateReview
} from "../services/reviewService";
import toast from "react-hot-toast";

export const REVIEW_KEYS = {
  all: ["reviews"],
  lists: () => [...REVIEW_KEYS.all, "list"],
  user: () => [...REVIEW_KEYS.all, "user"],
  userAll: () => [...REVIEW_KEYS.user(), "all"],
};

// Hook to submit a new review
export function useSubmitReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ productId, rating, comment }) =>
      submitReview(productId, rating, comment),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: REVIEW_KEYS.userAll() });

      toast.success("Review submitted successfully");
    },

    onError: (error) => {
      console.error("Failed to submit review:", error);
      toast.error(error.response?.data?.message || "Failed to submit review.");
    }
  });
}

// Hook to fetch reviews submitted by the user
export function useFetchUserReview() {
  return useQuery({
    queryKey: REVIEW_KEYS.userAll(),
    queryFn: fetchUserReviews,

    onError: (error) => {
      console.error("Failed to fetch user reviews:", error);
      toast.error(error.response?.data?.message || "Failed to fetch user reviews.");
    }
  });
}

// Hook to update an existing review
export function useUpdateReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reviewId, rating, comment }) =>
      updateReview(reviewId, rating, comment),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: REVIEW_KEYS.userAll() });
      toast.success("Review updated successfully!");
    },

    onError: (error) => {
      console.error("Failed to update review:", error);
      toast.error(error.response?.data?.message || "Failed to update review.");
    }
  });
}

// Hook to delete a review
export function useDeleteReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewId) => deleteReview(reviewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: REVIEW_KEYS.userAll() });
      toast.success("Review deleted successfully!");
    },
    onError: (error) => {
      console.error("Failed to delete review:", error);
      toast.error(error.response?.data?.message || "Failed to delete review.");
    }
  });
}