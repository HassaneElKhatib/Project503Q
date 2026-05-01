import { FaStar } from "react-icons/fa";
const FALLBACK_IMAGE =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400'><rect width='100%25' height='100%25' fill='%23f3f4f6'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-family='Arial' font-size='24'>No image</text></svg>";

export default function ReviewPopup({ index, item, onClose, setRating, rating, setComment, comment, handleSubmitReview }){
  return(
    <div>
      <div key={index} className="fixed top-0 left-0 w-full h-full bg-[#00000050] flex justify-center items-center z-50">
        <div className="w-[400px] bg-white rounded-2xl p-6 relative">
          {/* Close button */}
          <button 
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl"
            onClick={ () => onClose() }
          >
            ×
          </button>

          {/* Header */}
          <div className="mb-5">
            <h2 className="text-xl font-bold text-gray-800">Rate & Review</h2>
            <h3 className="text-sm text-gray-500">Share your experience with this product</h3>
          </div>

          <div className="my-3">
            <h1 className="text-sm font-semibold mb-2">Items</h1>
            <div className="flex flex-row gap-2">
              <img src={item.image || FALLBACK_IMAGE} alt={item.name} className="w-16 h-16 object-cover rounded-md flex-shrink-0"/>
              <span className="text-sm text-secondary pt-5">{item.name}</span>
            </div>
          </div>

          {/* Rating */}
          <div className="mb-3">
            <h2 className="text-sm font-semibold text-gray-700 mb-1">Rating</h2>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  className="text-4xl focus:outline-none transition-colors cursor-pointer"
                  onClick={ () => {setRating(star)}}
                >
                  <span className={`${rating >= star ? "text-yellow-500" : "text-gray-300"}`}><FaStar /></span>
                </button>
              ))}
            </div>
          </div>

          {/* Your Review */}
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Your Review</h2>
            <textarea 
              placeholder="Share your thoughts about this order..."
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm h-24 resize-none focus:outline-none focus:border-purple-500"
              onChange={ (e) => {setComment(e.target.value)}}
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            <button 
              className="flex-1 border-2 border-gray-300 text-gray-700 font-medium py-2 rounded-lg hover:bg-gray-200 transition- hover:cursor-pointer"
              onClick={ () => onClose()}
            >
              Cancel
            </button>
            <button 
              className="flex-1 bg-accent-hover text-white font-medium py-2 rounded-lg border-2 hover:bg-white hover:text-accent-hover hover:border-2 hover:border-accent-hover transition-colors hover:cursor-pointer"
              onClick={ () => handleSubmitReview(rating, comment)}
            >
              Submit Review
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}