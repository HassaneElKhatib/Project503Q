import { IoMdCheckmarkCircleOutline } from "react-icons/io";
import { RiArrowDropDownLine } from "react-icons/ri";
import { useEffect, useState } from "react";
import axios from "axios";
import { optionalBearerHeaders } from "../../config/axiosConfig";
import { publicApiOrigin } from "../../utils/publicApiOrigin";
import { useNavigate } from "react-router-dom";
import Loader from "../../components/loader";
import { TbTruckDelivery } from "react-icons/tb";
import { MdOutlineWatchLater } from "react-icons/md";
import ReviewPopup from "../../components/review/reviewPopup";
import toast from "react-hot-toast";
import CancelOrderModal from "../../components/CancelOrderModal";

const FALLBACK_IMAGE =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400'><rect width='100%25' height='100%25' fill='%23f3f4f6'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-family='Arial' font-size='24'>No image</text></svg>";

function normalizeStatus(status) {
  const value = (status || "").toLowerCase();
  if (value === "completed" || value === "delivered") return "Delivered";
  if (value === "cancelled" || value === "canceled") return "Cancelled";
  if (value === "shipped") return "Shipped";
  if (value === "processing") return "Processing";
  if (value === "confirmed") return "Confirmed";
  if (value === "returned") return "Returned";
  return "Pending";
}

function formatAddress(address) {
  if (!address || typeof address !== "object") return "";
  return [address.name, address.line1, address.line2, address.city, address.postalCode, address.country]
    .filter(Boolean)
    .join(", ");
}

export default function OrdersHistoryPage() {
  const navigate = useNavigate();
  const [isExpanded, setIsExpanded] = useState({});
  const [orders, setOrders] = useState([]);
  const [page, setPage] = useState(1);
  const [limit] = useState(5);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [orderCount, setOrderCount] = useState(0);
  const [popupVisible, setPopupVisible] = useState(false);

  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [selectedItem, setSelectedItem] = useState(null);
  const [reviewSent, setReviewSent] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelingOrderId, setCancelingOrderId] = useState(null);
  const [returnReasonByOrder, setReturnReasonByOrder] = useState({});


  useEffect(() => {

    if(isLoading){
      axios.get(`${publicApiOrigin()}/api/orders/history/${page}/${limit}`,
    {
      headers: optionalBearerHeaders(),
      withCredentials: true,
    }).then((res) => {
      setOrders(res.data.orders || []);
      setTotalPages(Math.max(1, Math.ceil((res.data.total || 0) / (res.data.limit || limit))));
      setOrderCount(res.data.total || 0);
      console.log(res.data);
      setIsLoading(false);
      console.log(page);
      console.log(res.data.totalPages);
      console.log(limit);

    }).catch((err) => {
      console.error(err);
      setIsLoading(false);
      if (err.response?.status === 401) {
        navigate("/login");
      }
    });

    }
    
  }, [isLoading, page]);

  async function handleSubmitReview(rating, comment) {
    try{
      console.log("selectedItem:", selectedItem);

      await axios.post(`${publicApiOrigin()}/api/reviews`, {
        productId: selectedItem.productId,
        rating: rating,
        comment: comment,

      },{
          headers: optionalBearerHeaders(),
          withCredentials: true,
      }).then((res) => {
        console.log("Review submitted successfully:", res.data);
        toast.success("Review submitted successfully!");
        setPopupVisible(false);
        setReviewSent(true);
        setRating(0);
        setComment("");

      }).catch((err) => {
        console.error("Failed to submit review:", err);
        toast.error("Failed to submit review.");
      });


    }catch(error){
      console.error("Failed to submit review:", error);
    }
  }

  const handleCancelOrder = async (orderId, reason) => {
    try {
      if (!reason || reason.trim() === "") {
        toast.error("Please provide a cancel reason");
        return;
      }

      console.log("Cancelling order:", orderId, "Reason:", reason);
      await axios.put(`${publicApiOrigin()}/api/orders/${orderId}`,
        { status: "cancelled" },
        {
          headers: optionalBearerHeaders(),
          withCredentials: true,
        }
      );

      toast.success("Order cancelled successfully");

      setShowCancelModal(false);
      setCancelingOrderId(null);
      setIsLoading(true);

    } catch (error) {
      console.error(error);
      toast.error(
        error.response?.data?.message || "Failed to cancel order"
      );
    }
  };          

  const handleRequestReturn = async (orderId) => {
    const reason = (returnReasonByOrder[orderId] || "").trim();
    if (!reason) {
      toast.error("Please provide a reason for return request");
      return;
    }
    try {
      await axios.post(
        `${publicApiOrigin()}/api/orders/${orderId}/returns`,
        { reason },
        {
          headers: optionalBearerHeaders(),
          withCredentials: true,
        }
      );
      toast.success("Return request submitted");
      setReturnReasonByOrder((prev) => ({ ...prev, [orderId]: "" }));
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to request return");
    }
  };

  const handleGetInvoice = async (orderId) => {
    try {
      const res = await axios.get(`${publicApiOrigin()}/api/orders/${orderId}/invoice`, {
        headers: optionalBearerHeaders(),
        withCredentials: true,
      });
      toast.success(`Invoice ready: ${res.data?.invoice?.invoiceId || "N/A"}`);
    } catch (error) {
      console.error(error);
      toast.error("Failed to fetch invoice");
    }
  };


  return(
    <div className="w-full min-h-screen flex flex-col items-center bg-primary pb-25 pt-5 px-4 sm:px-6 lg:px-8 relative">
      {!isLoading ? 
        (<div className="w-full max-w-4xl">
          <div className="mb-6 sm:mb-8">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-secondary mb-2">Order History</h1>
            <p className="text-sm sm:text-base text-secondary">Track and manage all your orders in one place</p>
          </div>
          {orders.map((order, index) => {
          return (
              <div key={index} className="flex flex-col bg-white rounded-xl sm:rounded-2xl shadow-lg overflow-hidden mb-4 sm:mb-5">
                {/* Order Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between w-full p-4 sm:p-6 border-b border-gray-100 gap-3 sm:gap-0">
                  <div className="flex-1">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 mb-2">
                      <h2 className="font-semibold text-lg sm:text-xl text-secondary">{order._id}</h2> 
                      {(() => {
                        const s = normalizeStatus(order.status);
                        if (s === "Delivered") return (
                          <span className="flex items-center gap-1.5 text-xs sm:text-sm font-medium text-green-600 bg-green-50 px-2 sm:px-3 py-1 rounded-full w-fit">
                            <IoMdCheckmarkCircleOutline className="text-base sm:text-[20px]" />
                            Delivered
                          </span>
                        );
                        if (s === "Shipped") return (
                          <span className="flex items-center gap-1.5 text-xs sm:text-sm font-medium text-blue-600 bg-blue-50 px-2 sm:px-3 py-1 rounded-full w-fit">
                            <TbTruckDelivery className="text-base sm:text-[20px]" />
                            Shipped
                          </span>
                        );
                        if (s === "Processing" || s === "Confirmed") return (
                          <span className="flex items-center gap-1.5 text-xs sm:text-sm font-medium text-indigo-600 bg-indigo-50 px-2 sm:px-3 py-1 rounded-full w-fit">
                            <MdOutlineWatchLater className="text-base sm:text-[20px]" />
                            {s}
                          </span>
                        );
                        if (s === "Cancelled" || s === "Returned") return (
                          <span className="flex items-center gap-1.5 text-xs sm:text-sm font-medium text-red-500 bg-red-50 px-2 sm:px-3 py-1 rounded-full w-fit">
                            <MdOutlineWatchLater className="text-base sm:text-[20px]" />
                            {s}
                          </span>
                        );
                        return (
                          <span className="flex items-center gap-1.5 text-xs sm:text-sm font-medium text-yellow-500 bg-yellow-50 px-2 sm:px-3 py-1 rounded-full w-fit">
                            <MdOutlineWatchLater className="text-base sm:text-[20px]" />
                            Pending
                          </span>
                        );
                      })()}
                    </div>
                    <p className="text-xs sm:text-sm text-secondary/60">Ordered on {new Date(order.createdAt).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}</p>
                  </div>
                  <div className="flex items-center justify-between sm:justify-end gap-3">
                    <h2 className="text-xl sm:text-2xl font-bold text-accent">${order.total.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}</h2>
                    <button 
                      onClick={() => setIsExpanded(
                        prev => ({
                          ...prev,
                          [order._id]: !prev[order._id]
                        })
                      )}
                      className="text-secondary/40 hover:text-secondary transition-colors"
                    >
                      <RiArrowDropDownLine className={`text-[40px] sm:text-[50px] transition-transform ${isExpanded[order._id] ? "rotate-180" : ""} hover:text-secondary hover:cursor-pointer`} />
                    </button>
                  </div>
                </div>

                {/* Expandable Content */}
                {isExpanded[order._id] && (
                  <div className="px-4 sm:px-6 pb-4 sm:pb-6 pt-4 border-t-2 border-accent-hover">
                    <h3 className="font-semibold text-base sm:text-lg text-secondary mb-3 sm:mb-4">Items</h3>
                    
                    {/* Items List */}
                    {order.items.map((item, itemIndex) => {
                      return(
                        
                          <div key={itemIndex} className="space-y-4 mb-4">
                            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center py-3 border-b border-gray-100 gap-3 sm:gap-0">
                              <div className="flex items-center gap-3 sm:gap-4">
                                <img
                                  src={item.image || FALLBACK_IMAGE}
                                  alt={item.name}
                                  className="w-12 h-12 sm:w-16 sm:h-16 object-cover rounded-md flex-shrink-0"
                                  onError={(e) => {
                                    e.currentTarget.onerror = null;
                                    e.currentTarget.src = FALLBACK_IMAGE;
                                  }}
                                />
                                <div>
                                  <h4 className="font-medium text-sm sm:text-base text-secondary mb-1">{item.name}</h4>
                                  <span className="text-xs sm:text-sm text-secondary/60">Qty: {item.quantity}</span>
                                </div>
                              </div>
                              <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-2">
                                <p className="font-semibold text-sm sm:text-base text-secondary">${(item.quantity * item.price).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                                <button className={`${normalizeStatus(order.status) !== "Delivered" ? "hidden" : "text-xs sm:text-sm font-bold text-accent-hover hover:text-accent cursor-pointer" }`}
                                onClick={() => {
                                  setPopupVisible(true);
                                  setSelectedItem(item);
                                }}
                                >
                                  {!reviewSent ? "Leave a Review" : "Review Sent"}
                                </button>
                              </div>
                            </div>
                          </div>        
                      )
                    })}

                    {/* Review popup */}
                      {
                        popupVisible && selectedItem &&(
                          <ReviewPopup item={selectedItem} onClose={ () => setPopupVisible(false) } rating={rating} setRating={setRating} comment={comment} setComment={setComment} handleSubmitReview={handleSubmitReview} index={index} />
                        )
                      }

                        {/* Delivery Info */}
                        <div className="flex flex-col sm:flex-row sm:justify-between border-t-2 border-accent-hover gap-4 sm:gap-6 pt-4 sm:pt-5 mb-4 sm:mb-6">
                          <div className="flex-1">
                            <h4 className="font-semibold text-sm sm:text-base text-secondary mb-2">Delivery Address</h4>
                            <p className="text-xs sm:text-sm text-secondary/70">{formatAddress(order.address)}</p>
                          </div>
                          <div className="flex-1">
                            <h4 className="font-semibold text-sm sm:text-base text-secondary mb-2">Estimated Delivery</h4>
                            <p className="text-xs sm:text-sm text-secondary/70">{new Date(order.createdAt).toLocaleDateString("en-US", {
                              year: "numeric",
                              month: "long",
                              day: "numeric",
                            })}</p>
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-4">
                          <button 
                          disabled={(order.status || "").toLowerCase() !== "pending"}
                          className={`flex-1 bg-red-500 border-2 border-gray-200 text-white font-medium py-2.5 sm:py-3 rounded-lg text-sm sm:text-base ${(order.status || "").toLowerCase() !== "pending" ? "opacity-50 cursor-not-allowed" : "hover:bg-gray-50 hover:border-red-500 hover:text-red-500 hover:cursor-pointer"}  transition-colors`}
                          onClick={() => {
                            setCancelingOrderId(order._id);
                            setShowCancelModal(true);
                          }}
                          >
                          Cancel Order
                          </button>
                           
                          
                          <button className="flex-1 bg-white border-2 border-gray-200 text-secondary font-medium py-2.5 sm:py-3 rounded-lg text-sm sm:text-base hover:bg-gray-300 hover:cursor-pointer hover:text-white transition-colors"
                            onClick={() => {navigate("/contactUs")}}
                          >
                            Contact Support
                          </button>
                          {normalizeStatus(order.status) === "Delivered" && (
                            <button
                              className="flex-1 bg-white border-2 border-accent text-accent font-medium py-2.5 sm:py-3 rounded-lg text-sm sm:text-base hover:bg-accent hover:text-white transition-colors"
                              onClick={() => handleGetInvoice(order._id)}
                            >
                              Get Invoice
                            </button>
                          )}
                        </div>

                        {normalizeStatus(order.status) === "Delivered" && (
                          <div className="mt-4 p-3 border rounded-lg bg-gray-50">
                            <p className="text-sm font-semibold mb-2">Request a return</p>
                            <textarea
                              className="w-full border rounded-md p-2 text-sm"
                              rows={2}
                              placeholder="Reason for return request"
                              value={returnReasonByOrder[order._id] || ""}
                              onChange={(e) =>
                                setReturnReasonByOrder((prev) => ({ ...prev, [order._id]: e.target.value }))
                              }
                            />
                            <button
                              className="mt-2 px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 text-sm"
                              onClick={() => handleRequestReturn(order._id)}
                            >
                              Submit Return Request
                            </button>
                          </div>
                        )}

                        {/* Cancel Order Modal */}
                        {showCancelModal && (
                          <CancelOrderModal
                            isOpen={showCancelModal}
                            onClose={() => setShowCancelModal(false)}
                            orderId={cancelingOrderId}
                            onSubmit={handleCancelOrder}
                          />
                        )}
                  </div>
                )}
              </div>
            
            )
          })
        
        }

        {/* Paginator */}
        <div className="flex flex-col sm:flex-row w-full items-center justify-between absolute bottom-0 right-0 rounded-lg p-4 mt-6 gap-3 sm:gap-0">
          <div className="text-xs sm:text-sm text-gray-600 text-center sm:text-left">
            Showing {((page - 1) * limit) + 1} to {Math.min(((page - 1) + limit), orderCount)} of {orderCount} orders
          </div>
          <div className="flex items-center justify-center w-full sm:w-[250px] rounded-xl h-[50px] shadow-2xl gap-3 sm:gap-4">
            <button
              onClick={() => {
                setPage(prev => Math.max(1, prev - 1));
                setIsLoading(true);
              }}
              disabled={page === 1}
              className="text-xs sm:text-sm text-gray-600 shadow-2xl hover:text-gray-900 disabled:text-gray-300 disabled:cursor-not-allowed flex items-center gap-1"
            >
              <span>❮</span> Previous
            </button>
            <span className="text-xs sm:text-sm text-gray-700 font-medium">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => {
                setPage(prev => Math.min(totalPages, prev + 1));
                setIsLoading(true);
              }}
              disabled={page === totalPages}
              className="text-xs sm:text-sm text-gray-600 hover:text-gray-900 disabled:text-gray-300 disabled:cursor-not-allowed flex items-center gap-1"
            >
              Next <span>❯</span>
            </button>
          </div>
        </div>
        </div>) : (<Loader />)
      }
    </div>
  )
}