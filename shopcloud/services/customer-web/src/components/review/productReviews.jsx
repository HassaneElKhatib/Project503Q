import { IoCheckmarkDone } from "react-icons/io5";
import { MdOutlineCancel } from "react-icons/md";
import { FaStar } from "react-icons/fa";

export function ProductReview({ reviews }) {
  if (!reviews || reviews.length === 0) {
    return (
      <div className="text-center text-2xl text-gray-500 py-10">
        No reviews available for this product yet.
      </div>
    );
  }

  const getReviewerName = (review) => {
    if (review?.userName) return review.userName;
    if (review?.userId?.firstName || review?.userId?.lastName) {
      return `${review.userId.firstName || ""} ${review.userId.lastName || ""}`.trim();
    }
    return "Anonymous";
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {reviews.map((review, index) => (
        <div key={index} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
          <div className="flex flex-row">
            <h2 className="font-semibold text-lg text-secondary">
              {getReviewerName(review)}
            </h2>
            {review.isVerifiedPurchase ? (
              <span className="text-sm text-green-800 ml-1 px-2 py-1 bg-green-200 rounded-xl">
                <IoCheckmarkDone className="inline-block mr-1" />
                Verified Purchase
              </span>
            ) : (
              <span className="text-sm text-red-800 ml-1 px-2 py-1 bg-red-200 rounded-xl">
                <MdOutlineCancel className="inline-block mr-1" />
                Not Verified
              </span>
            )}
          </div>
          <div className="flex">
            {[1, 2, 3, 4, 5].map((star) => (
              <FaStar
                key={star}
                className={`my-1 ${review.rating >= star ? "text-yellow-500" : "text-gray-300"}`}
              />
            ))}
          </div>
          <p className="text-secondary/70 leading-relaxed">{review.comment}</p>
        </div>
      ))}
    </div>
  );
}
