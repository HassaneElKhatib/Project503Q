import { useState } from "react";
import { IoMdCheckmarkCircleOutline } from "react-icons/io";
import { RiArrowDropDownLine } from "react-icons/ri";
import { TbTruckDelivery } from "react-icons/tb";
import { MdOutlineWatchLater } from "react-icons/md";
import TitleHeaderDashboard from "../../../components/TitleHeader";
import Loader from "../../../components/loader";
import ReviewPopup from "../../../components/review/reviewPopup";
import { useOrders } from "../../../hooks/useOrderQueries";
import { useSubmitReview } from "../../../hooks/useReviewQueries";

export default function MyOrdersPage() {
  const [isExpanded, setIsExpanded] = useState({});
  const [page, setPage] = useState(1);
  const [limit] = useState(5);
  const [popupVisible, setPopupVisible] = useState(false);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [selectedItem, setSelectedItem] = useState(null);
  const [reviewSent, setReviewSent] = useState(false);

  const { data, isLoading, isError, error } = useOrders(page, limit);
  const orders = data?.orders || [];
  const totalPages = Math.max(1, Math.ceil((data?.total || 0) / (data?.limit || limit)));
  const orderCount = data?.total || 0;

  const submitReviewMutation = useSubmitReview();

  const handleSubmitReview = async (rating, comment) => {
    submitReviewMutation.mutate(
      {
        productId: selectedItem.productId,
        rating,
        comment,
      },
      {
        onSuccess: () => {
          setPopupVisible(false);
          setRating(0);
          setComment("");
          setSelectedItem(null);
          setReviewSent(true);
        }
      }
    );
  };

  const getStatusBadge = (status) => {
    const normalized = (status || "").toLowerCase();
    if (normalized === "completed" || normalized === "delivered") {
      return (
        <span className="flex items-center gap-1.5 text-sm font-medium text-green-600 bg-green-50 px-3 py-1.5 rounded-full">
          <IoMdCheckmarkCircleOutline className="text-[18px]" />
          Delivered
        </span>
      );
    } else if (normalized === "pending") {
      return (
        <span className="flex items-center gap-1.5 text-sm font-medium text-yellow-600 bg-yellow-50 px-3 py-1.5 rounded-full">
          <TbTruckDelivery className="text-[18px]" />
          Pending
        </span>
      );
    } else {
      return (
        <span className="flex items-center gap-1.5 text-sm font-medium text-red-600 bg-red-50 px-3 py-1.5 rounded-full">
          <MdOutlineWatchLater className="text-[18px]" />
          Cancelled
        </span>
      );
    }
  };

  const formatAddress = (address) => {
    if (!address || typeof address !== "object") return "";
    return [address.name, address.line1, address.line2, address.city, address.postalCode, address.country]
      .filter(Boolean)
      .join(", ");
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] px-10">
        <div className="text-red-500 text-6xl mb-4">⚠️</div>
        <h2 className="text-2xl font-semibold text-gray-800 mb-2">
          Oops! Something went wrong
        </h2>
        <p className="text-gray-600 mb-6">
          {error?.message || 'Failed to load your orders'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="bg-accent text-white px-6 py-3 rounded-lg hover:bg-accent-hover"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative flex flex-col">
      <TitleHeaderDashboard 
        title="My Orders" 
        subtitle="Track and manage all your orders"
      />

      {/* Orders List */}
      <div className="px-10 mt-6 space-y-5 flex-1 mb-5">
        {orders.length > 0 ? (
          orders.map((order) => (
            <div 
              key={order._id} 
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden transition-shadow hover:shadow-md"
            >
              {/* Order Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-100">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="font-semibold text-lg text-gray-800">
                      {order._id}
                    </h2>
                    {getStatusBadge(order.status)}
                  </div>
                  <p className="text-sm text-gray-500">
                    Ordered on {new Date(order.createdAt).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-500 mb-1">Total Amount</p>
                    <h3 className="text-2xl font-bold text-accent">
                      $ {order.total.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </h3>
                  </div>
                  <button
                    onClick={() =>
                      setIsExpanded((prev) => ({
                        ...prev,
                        [order._id]: !prev[order._id],
                      }))
                    }
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <RiArrowDropDownLine
                      className={`text-[48px] transition-transform duration-200 ${
                        isExpanded[order._id] ? "rotate-180" : ""
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Expandable Content */}
              {isExpanded[order._id] && (
                <div className="p-6 bg-gray-50">
                  <h3 className="font-semibold text-base text-gray-800 mb-4">
                    Order Items
                  </h3>

                  {/* Items List */}
                  <div className="space-y-3 mb-6">
                    {order.items.map((item, itemIndex) => (
                      <div
                        key={itemIndex}
                        className="flex justify-between items-center p-4 bg-white rounded-lg border border-gray-200"
                      >
                        <div className="flex items-center gap-4">
                          <img
                            src={item.image}
                            alt={item.name}
                            className="w-16 h-16 object-cover rounded-md border border-gray-200"
                          />
                          <div>
                            <h4 className="font-medium text-gray-800 mb-1">
                              {item.name}
                            </h4>
                            <p className="text-sm text-gray-500">
                              Qty: {item.quantity} × $ {item.price.toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <p className="font-semibold text-gray-800">
                            $ {(item.quantity * item.price).toLocaleString()}
                          </p>
                          {(order.status || "").toLowerCase() === "completed" && (
                            <button
                              onClick={() => {
                                setPopupVisible(true);
                                setSelectedItem(item);
                              }}
                              className="text-sm font-medium text-accent hover:text-accent-hover transition-colors cursor-pointer"
                            >
                              {reviewSent ? "Review Sent ✓" : "Leave a Review"}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Delivery Info */}
                  <div className="grid md:grid-cols-2 gap-6 mb-6 p-4 bg-white rounded-lg border border-gray-200">
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                        <TbTruckDelivery className="text-accent" />
                        Delivery Address
                      </h4>
                      <p className="text-sm text-gray-600">{formatAddress(order.address)}</p>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-2">
                        Estimated Delivery
                      </h4>
                      <p className="text-sm text-gray-600">
                        {new Date(order.createdAt).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        })}
                      </p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-4">
                    <button
                      disabled={(order.status || "").toLowerCase() !== "pending"}
                      className={`flex-1 font-medium py-3 rounded-lg transition-colors ${
                        (order.status || "").toLowerCase() !== "pending"
                          ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                          : "bg-red-500 text-white hover:bg-red-600"
                      }`}
                    >
                      Cancel Order
                    </button>
                    <button className="flex-1 bg-white border-2 border-gray-300 text-gray-700 font-medium py-3 rounded-lg hover:bg-gray-100 transition-colors">
                      Contact Support
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-5">
            <div className="text-gray-400 mb-4">
              <TbTruckDelivery size={64} className="mx-auto opacity-50" />
            </div>
            <h3 className="text-xl font-semibold text-gray-600 mb-2">
              No Orders Yet
            </h3>
            <p className="text-gray-500">
              Start shopping to see your orders here!
            </p>
          </div>
        )}
      </div>

      {/* Review Popup */}
      {popupVisible && selectedItem && (
        <ReviewPopup
          item={selectedItem}
          onClose={() => setPopupVisible(false)}
          rating={rating}
          setRating={setRating}
          comment={comment}
          setComment={setComment}
          handleSubmitReview={handleSubmitReview}
        />
      )}

      {/* Pagination */}
      {orders.length > 0 && (
        <div className="flex items-center justify-between px-10 mt-auto w-full">
          <div className="text-sm text-gray-600">
            Showing {(page - 1) * limit + 1} to{" "}
            {Math.min(page * limit, orderCount)} of {orderCount} orders
          </div>
          <div className="flex items-center gap-4 bg-white rounded-lg shadow-sm px-6 py-3 border border-gray-200">
            <button
              onClick={() => {
                setPage((prev) => Math.max(1, prev - 1));
              }}
              disabled={page === 1}
              className="text-gray-600 hover:text-gray-900 disabled:text-gray-300 disabled:cursor-not-allowed flex items-center gap-1 transition-colors"
            >
              <span>❮</span> Previous
            </button>
            <span className="text-sm text-gray-700 font-medium px-4">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => {
                setPage((prev) => Math.min(totalPages, prev + 1));
              }}
              disabled={page === totalPages}
              className="text-gray-600 hover:text-gray-900 disabled:text-gray-300 disabled:cursor-not-allowed flex items-center gap-1 transition-colors"
            >
              Next <span>❯</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}