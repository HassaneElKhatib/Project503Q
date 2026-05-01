import { useState } from "react";
import { FaStar } from "react-icons/fa";

export default function SiteReviewForm({
  initialRating,
  initialComment,
  onSubmit,
  submitText,
  isSubmitting,
}) {
  const [rating, setRating] = useState(initialRating);
  const [comment, setComment] = useState(initialComment);

  return (
    <div className="fixed top-0 left-0 w-full h-full bg-[#00000050] flex justify-center items-center z-50">
      <div className="bg-white p-8 rounded-2xl shadow-md w-120">
        <h2 className="text-2xl font-serif text-gray-800 mb-6">
          Leave a Review
        </h2>

        {/* Stars */}
        <div className="flex gap-2 mb-6">
          {[1, 2, 3, 4, 5].map((star) => (
            <FaStar
              key={star}
              onClick={() => setRating(star)}
              className={`cursor-pointer text-xl ${
                star <= rating ? "text-accent" : "text-gray-300"
              }`}
            />
          ))}
        </div>

        {/* Comment */}
        <textarea
          rows="5"
          maxLength={300}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Share your experience with our website..."
          className="w-full border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-accent"
        />

        {/* Submit */}
        <button
          className="mt-6 w-full bg-accent text-white py-2 rounded-lg font-medium hover:bg-accent-hover transition cursor-pointer disabled:opacity-60"
          onClick={() => onSubmit({ rating, comment })}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Please wait..." : submitText}
        </button>

        <p className="text-xs text-gray-400 mt-3">
          Reviews are about your experience with our website, not individual products.
        </p>
      </div>
    </div>
  );
}
