import { useEffect, useState } from "react";
import { FaStar } from "react-icons/fa";
import TitleHeaderDashboard from "../../components/TitleHeader";
import { deleteReview, fetchAllReviews } from "../../services/reviewService";
import { fetchSiteReviews, updateSiteReviewStatus } from "../../services/siteReviewService";
import toast from "react-hot-toast";

export default function ReviewsManagementPage() {
  const [activeTab, setActiveTab] = useState("product");
  const [, setIsLoading] = useState(true);
  const [productReviews, setProductReviews] = useState([]);
  const [siteReviews, setSiteReviews] = useState([]);

  useEffect( () => {
      const getProductReviews = async () => {
        setIsLoading(true);
        try {
          const response = await fetchAllReviews();
          setProductReviews(response);
          setIsLoading(false);
        } catch (error) {
          console.error("Error fetching product reviews:", error);
          setIsLoading(false);
        }
      }
      getProductReviews();
  }, []);

  useEffect(() => {
    const getSiteReviews = async () => {
      setIsLoading(true);
      try {
        const siteReviewsData = await fetchSiteReviews();
        setSiteReviews(siteReviewsData);
        console.log(siteReviewsData);
        setIsLoading(false);
      } catch (error) {
        console.error("Error fetching site reviews:", error);
        setIsLoading(false);
      }
    }
    getSiteReviews();
  }, []);

  const handleDeleteReview = async (reviewId) => {
    setIsLoading(true);
    try {
      const response = await deleteReview(reviewId);
      console.log(response);
      setProductReviews(response.reviews);
      toast.success("Review deleted successfully");

      setIsLoading(false);
    } catch (error) {
      console.error("Error deleting review:", error);
      toast.error("Failed to delete review");
      setIsLoading(false);
    }
  }

  const handleChangeSiteReviewStatus = async (reviewId, isApproved) => {
    try {
      await updateSiteReviewStatus(reviewId, isApproved);
      toast.success(`Site review ${isApproved ? "approved" : "unapproved"} successfully`);
      
      setSiteReviews(prevReviews => 
        prevReviews.map(review => 
          review._id === reviewId ? { ...review, isApproved: isApproved } : review
        )
      )

    } catch (error) {
      console.error("Error updating site review status:", error);
      toast.error("Failed to update site review status");
    }
  }

  return (
    <div className="mx-auto">
      <TitleHeaderDashboard
        title="Reviews Management"
        subtitle="Manage product and site reviews"
      />

      {/* Tabs */}
      <div className="flex gap-4 mb-6">
        <button
          className={`px-4 py-2 rounded-lg font-medium cursor-pointer  ${
            activeTab === "product"
              ? "bg-accent text-white"
              : "bg-gray-200 "
          }`}
          onClick={() => setActiveTab("product")}
        >
          Product Reviews
        </button>

        <button
          className={`px-4 py-2 rounded-lg font-medium cursor-pointer ${
            activeTab === "site"
              ? "bg-accent text-white"
              : "bg-gray-200"
          }`}
          onClick={() => setActiveTab("site")}
        >
          Site Reviews
        </button>
      </div>

      {/* PRODUCT REVIEWS */}
      {activeTab === "product" && (
        <div className="space-y-4 p-5 max-h-[600px] overflow-y-auto">
          {productReviews.map((review) => (
            <div
              key={review._id}
              className="bg-white p-4 rounded-xl shadow flex justify-between items-center"
            >
              <div>
                <p className="text-sm font-semibold">
                  Product: {review.productId}
                </p>
                <p className="text-xs text-gray-500">
                  User: {review.userEmail || review.userName || review.userId}
                </p>

                <div className="flex gap-1 my-1">
                  {[...Array(review.rating)].map((_, i) => (
                    <FaStar key={i} className="text-yellow-500 text-sm" />
                  ))}
                </div>

                <p className="text-sm">{review.comment}</p>

                {review.isApproved && (
                  <span className="text-xs text-green-600 font-medium">
                    ✔ Approved
                  </span>
                )}
              </div>

              <button className="text-white bg-red-500 text-sm hover:bg-red-400 mr-5 px-5 py-2 rounded-xl shadow-lg cursor-pointer"
                onClick={() => handleDeleteReview(review._id)}
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}

      {/* SITE REVIEWS */}
      {activeTab === "site" && (
        <div className="space-y-4 p-5 max-h-[600px] overflow-y-auto">
          {siteReviews.map((review) => (
            <div
              key={review._id}
              className="bg-white p-4 rounded-xl shadow flex justify-between items-center"
            >
              <div>
                <p className="text-sm font-semibold">
                  User: {review.userEmail || review.userName || review.userId}
                </p>

                <div className="flex gap-1 my-1">
                  {[...Array(review.rating)].map((_, i) => (
                    <FaStar key={i} className="text-yellow-500 text-sm" />
                  ))}
                </div>

                <p className="text-sm">{review.comment}</p>

                <p className="text-xs text-gray-400">
                  {new Date(review.createdAt).toLocaleString()}
                </p>
              </div>

              <div>
                {!review.isApproved ? (
                  <div className="flex flex-col justify-center items-center ml-2">
                    <span className="text-red-500 text-sm font-semibold mb-3">
                      Unapprove
                    </span>
                    <button
                      className="bg-green-500 px-3 py-1 rounded-lg text-white shadow-xl cursor-pointer hover:bg-green-400"
                      onClick={() => handleChangeSiteReviewStatus(review._id, true)}
                    >
                      Approve
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col justify-center items-center ml-2">
                    <span className="text-green-600 text-sm font-semibold mb-3">
                      Approved
                    </span>
                    <button className="bg-red-500 px-3 py-1 rounded-lg text-white shadow-xl cursor-pointer hover:bg-red-400"
                      onClick={() => handleChangeSiteReviewStatus(review._id, false)}
                    >Unapprove</button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
