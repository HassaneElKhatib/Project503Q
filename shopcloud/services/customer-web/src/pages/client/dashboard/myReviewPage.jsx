import { useState } from "react";
import { FaStar, FaEdit, FaTrash } from "react-icons/fa";
import TitleHeaderDashboard from "../../../components/TitleHeader";
import { useDeleteSiteReview, useUpdateSiteReview, useUserSiteReviewQueries } from "../../../hooks/useSiteReviewQueries";
import {  useDeleteReview, useFetchUserReview, useUpdateReview } from "../../../hooks/useReviewQueries";
import EditReviewPopup from "../../../components/review/editReviewPopup";
import SiteReviewForm from "../../../components/review/editSiteReviewForm";

export default function ClientMyReviews() {
  const [activeTab, setActiveTab] = useState("product");
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [editingReview, setEditingReview] = useState(null);
  const [deletingReview, setDeletingReview] = useState(null);

  const { data: siteReviewsData } = useUserSiteReviewQueries();
  const { data: userReviewsData } = useFetchUserReview();
  const reviews = activeTab === "product" ? userReviewsData || [] : siteReviewsData || [];
  // Mutations for product reviews
  const updateReviewMutation = useUpdateReview();
  const deleteReviewMutation = useDeleteReview();

  // Mutation for updating site reviews
  const updateSiteReviewMutation = useUpdateSiteReview();
  const deleteSiteReviewMutation = useDeleteSiteReview();

  const handleUpdateReview = async (reviewId, rating, comment) => {
    try {
      await updateReviewMutation.mutateAsync({ reviewId, rating, comment });
      setIsEditing(false);
    } catch (error) {
      console.error("Error updating review:", error);
    }
    setEditingReview(null);
  }

  const handleUpdateSiteReview = async ({ rating, comment }) => {
    if (!editingReview?._id) return;

    try {
      await updateSiteReviewMutation.mutateAsync({
        reviewId: editingReview._id,
        rating,
        comment,
      });
      setIsEditing(false);
    } catch (error) {
      console.error("Error updating site review:", error);
    } finally {
      setEditingReview(null);
    }
  };


  const handleDeleteReview = async (reviewId) => {
    try {
      await deleteReviewMutation.mutateAsync(reviewId);
      setIsDeleting(false);
    } catch (error) {
      console.error("Error deleting review:", error);
    }
    setDeletingReview(null);
  };

  const handleDeleteSiteReview = async (reviewId) => {
    try {
      await deleteSiteReviewMutation.mutateAsync(reviewId);
      setIsDeleting(false);
    } catch (error) {
      console.error("Error deleting site review:", error);
    }
    setDeletingReview(null);
  };

  return (
    <div>
      <TitleHeaderDashboard 
        title="My Reviews" 
        subtitle="Manage your product and site reviews"
      />
    
      <div className="p-6 bg-white rounded-xl shadow-sm">

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab("product")}
            className={`px-4 py-2 rounded-lg text-sm font-medium cursor-pointer hover:bg-accent-hover hover:text-white ${
              activeTab === "product"
                ? "bg-accent text-white"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            Product Reviews
          </button>

          <button
            onClick={() => setActiveTab("site")}
            className={`px-4 py-2 rounded-lg text-sm font-medium cursor-pointer hover:bg-accent-hover hover:text-white ${
              activeTab === "site"
                ? "bg-accent text-white"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            Site Reviews
          </button>
        </div>

        {/* Reviews List */}
        <div className="max-h-[420px] overflow-y-auto space-y-4 pr-2">
          {reviews.length === 0 ? (
            <p className="text-gray-500 text-sm">No reviews found.</p>
          ) : (
            reviews.map((review) => (
              <div
                key={review._id}
                className="rounded-lg p-4 flex justify-between gap-4 shadow-lg bg-gray-100"
              >
                <div className="flex-1">
                  {activeTab === "product" && (
                    <h4 className="font-medium mb-1">
                      {review.productName || review.productId}
                    </h4>
                  )}

                  {/* Rating */}
                  <div className="flex items-center gap-1 mb-2">
                    {[...Array(5)].map((_, i) => (
                      <FaStar
                        key={i}
                        className={`text-sm ${
                          i < review.rating
                            ? "text-yellow-400"
                            : "text-gray-300"
                        }`}
                      />
                    ))}
                  </div>

                  <p className="text-sm text-gray-700 mb-1">
                    {review.comment}
                  </p>

                  <span className="text-xs text-gray-400">
                    {new Date(review.createdAt).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </span>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-3">
                  <button
                    className="text-blue-500 hover:text-blue-700 cursor-pointer"
                    title="Edit Review"
                    onClick={() => {
                      setEditingReview(review);
                      setIsEditing(true);
                    }}
                  >
                    <FaEdit />
                  </button>
                  <button
                    className="text-red-500 hover:text-red-700 cursor-pointer"
                    title="Delete Review"
                    onClick={() => {
                      setDeletingReview(review);
                      setIsDeleting(true);
                    }}
                  >
                    <FaTrash />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Edit Review Popup */}
      {isEditing && activeTab === "product" && editingReview && (
        <EditReviewPopup
          item={{ name: editingReview.productName || editingReview.productId || "Product" }}
          review={editingReview}
          onClose={() => setIsEditing(false)}
          handleUpdateReview={handleUpdateReview}
        />
      )}

      {isEditing && activeTab === "site" && editingReview && (
        <SiteReviewForm
          initialRating={editingReview.rating}
          initialComment={editingReview.comment}
          onSubmit={handleUpdateSiteReview}
          submitText="Update Review"
          isSubmitting={updateSiteReviewMutation.isLoading}
        />
      )}

      {/* Delete Review Popup */}
      {isDeleting && (
        <div className="fixed bg-black/30 top-0 left-0 w-full h-full flex justify-center items-center z-50">
          <div className="flex p-8 flex-col items-center bg-white w-150 h-40 rounded-2xl">
            <h1 className="mb-5 text-xl">Are you sure you want to delete this review?</h1>
            <div className="flex gap-2">
              <button className="bg-accent p-3 w-40 rounded-xl text-white cursor-pointer hover:bg-accent-hover"
                onClick={() => {
                  if (activeTab === "product") {
                    handleDeleteReview(deletingReview._id);
                  } else {
                    handleDeleteSiteReview(deletingReview._id);
                  }
                }}
              >
                Yes, Delete Review
              </button>
              <button className="bg-gray-300 p-3 w-40 rounded-xl text-gray-700 cursor-pointer hover:bg-gray-400"
                onClick={() => setIsDeleting(false)}
              >
                No, Cancel
              </button>
            </div>
          </div>
          
        </div>
      )}
    </div>
  );
}
