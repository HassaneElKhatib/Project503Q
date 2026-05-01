import { useEffect, useState } from "react";
import { FaStar } from "react-icons/fa";

export default function EditReviewPopup({
  item,
  review,          
  onClose,
  handleUpdateReview
}) {

  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (review) {
      setRating(review.rating);
      setComment(review.comment);
    }
  }, [review]);

  return (
    <div className="fixed top-0 left-0 w-full h-full bg-[#00000050] flex justify-center items-center z-50">
      <div className="w-[400px] bg-white rounded-2xl p-6 relative">

        {/* Close */}
        <button
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl"
          onClick={onClose}
        >
          ×
        </button>

        {/* Header */}
        <div className="mb-5">
          <h2 className="text-xl font-bold text-gray-800">
            {isEditing ? "Edit Review" : "Your Review"}
          </h2>
          <p className="text-sm text-gray-500">
            {isEditing ? "Update your review" : "View your submitted review"}
          </p>
        </div>

        {/* Item */}
        <div className="my-3">
          <h1 className="text-sm font-semibold mb-2">Item</h1>
          <div className="flex gap-2">
            <img
              src={item.images[0]}
              alt={item.name}
              className="w-16 h-16 object-cover rounded-md"
            />
            <span className="text-sm pt-5">{item.name}</span>
          </div>
        </div>

        {/* Rating */}
        <div className="mb-3">
          <h2 className="text-sm font-semibold mb-1">Rating</h2>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                disabled={!isEditing}
                onClick={() => setRating(star)}
                className={`text-3xl transition-colors ${
                  isEditing ? "cursor-pointer" : "cursor-default"
                }`}
              >
                <FaStar
                  className={rating >= star ? "text-yellow-500" : "text-gray-300"}
                />
              </button>
            ))}
          </div>
        </div>

        {/* Comment */}
        <div className="mb-6">
          <h2 className="text-sm font-semibold mb-2">Your Review</h2>
          <textarea
            value={comment}
            disabled={!isEditing}
            onChange={(e) => setComment(e.target.value)}
            className={`w-full border rounded-lg px-4 py-3 text-sm h-24 resize-none
              ${isEditing ? "border-gray-300" : "bg-gray-100 cursor-not-allowed"}
            `}
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            className="flex-1 bg-gray-200 py-2 rounded-lg cursor-pointer hover:bg-gray-300"
            onClick={onClose}
          >
            Cancel
          </button>

          {!isEditing ? (
            <button
              className="flex-1 bg-accent text-white py-2 rounded-lg cursor-pointer hover:bg-accent-hover"
              onClick={() => setIsEditing(true)}
            >
              Edit Review
            </button>
          ) : (
            <button
              className="flex-1 bg-green-600 text-white py-2 rounded-lg cursor-pointer"
              onClick={() => handleUpdateReview(review._id, rating, comment)}
            >
              Update Review
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
