import { useState } from "react";
import { FaStar, FaQuoteLeft } from "react-icons/fa";
import toast from "react-hot-toast";
import { useCreateSiteReview, useSiteReviewQueries } from "../../hooks/useSiteReviewQueries";
import dayJs from "../../utils/dayjs";

export default function SiteReviews() {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  const { mutate: createSiteReview } = useCreateSiteReview();
  const { data: siteReviews } = useSiteReviewQueries();
  let reviewsCount = 0;

  const handleSubmit = (rating, comment) => {

    if (!rating || !comment.trim()) {
      toast.error("Please provide a rating and comment.");
      return;
    }

    createSiteReview({ rating, comment: comment.trim() });
    setRating(0);
    setComment("");
  }

  if (siteReviews?.length <= 3) {
    reviewsCount = siteReviews?.length; 
  }else {
    reviewsCount = 3;
  }

  console.log("Site Reviews:", siteReviews);

  return (
      <div className="flex-1 pt-5 pb-10 bg-primary">
        <div className="max-w-6xl mx-auto px-4">

          {/* Page Header */}
          <div className="text-center mb-16">
            <h1 className="text-4xl font-serif text-gray-800 mb-4">
              Community Feedback
            </h1>
            <p className="text-gray-600 max-w-2xl mx-auto">
              See what our customers say about their experience with ShopCloud
              and share your thoughts with us.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-16 items-start">

            {/* Review Form */}
            <div className="lg:sticky lg:top-28">
              <div className="bg-white p-8 rounded-2xl shadow-md">
                <h2 className="text-2xl font-serif text-gray-800 mb-6">
                  Leave a Review
                </h2>

                <div className="flex gap-2 mb-6">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <FaStar
                      key={star}
                      onClick={() => setRating(star)}
                      className={`cursor-pointer text-xl ${
                        star <= rating
                          ? "text-accent"
                          : "text-gray-300"
                      }`}
                    />
                  ))}
                </div>

                <textarea
                  rows="5"
                  maxLength={300}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Share your experience with our website..."
                  className="w-full border rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-accent"
                />

                <button
                  className="mt-6 w-full bg-accent text-white py-2 rounded-lg font-medium hover:bg-accent-hover transition cursor-pointer"
                  onClick={ () => handleSubmit(rating, comment) }
                >
                  Submit Review
                </button>

                <p className="text-xs text-gray-400 mt-3">
                  Reviews are about your experience with our website, not individual products.
                </p>
              </div>
            </div>

            {/* Reviews List */}
            <div className="space-y-8">
              <h2 className="text-2xl font-serif text-gray-800 flex items-center gap-3">
                <FaStar className="text-accent" />
                Top Rated Experiences
              </h2>

              {siteReviews?.map((review) => (
                <div
                  key={review._id}
                  className="bg-white p-8 rounded-2xl shadow-sm  relative"
                >
                  <FaQuoteLeft className="absolute top-4 right-4 text-accent/10 text-5xl" />

                  <div className="flex items-center gap-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <FaStar
                        key={i}
                        className={`text-sm ${
                          i < review.rating
                            ? "text-accent"
                            : "text-gray-300"
                        }`}
                      />
                    ))}
                  </div>

                  <p className="text-gray-700 italic mb-6">
                    "{review.comment}"
                  </p>

                  <div className="flex justify-between items-center border-t pt-4">
                    <div>
                      <p className="font-serif text-gray-800">
                        {review.userName || "Anonymous"}
                      </p>
                      {review.isApproved && (
                        <span className="text-[10px] uppercase tracking-widest text-gray-400">
                          Approved
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">
                      {dayJs(review.createdAt).fromNow()}
                    </span>
                  </div>
                </div>
              ))}

              <div className="bg-white p-6 rounded-xl text-center shadow-sm">
                <p className="text-sm text-gray-500">
                  Showing {reviewsCount}  of {siteReviews?.length} verified site reviews
                </p>
              </div>
            </div>

          </div>
        </div>
      </div>
    
  );
}
