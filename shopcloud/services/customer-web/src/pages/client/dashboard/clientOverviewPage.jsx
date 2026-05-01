import { FaShoppingCart, FaCheckCircle, FaClock, FaTimesCircle, FaStar } from "react-icons/fa";
import TitleHeaderDashboard from "../../../components/TitleHeader";
import Card from "../../../components/Card";
import { Link } from "react-router-dom";
import { useClientDashboard } from "../../../hooks/useDashboardQueries";
import { useUser } from "../../../hooks/useUserQueries";
import Loader from "../../../components/loader";
import dayjs from "../../../utils/dayjs";



export default function ClientDashboardOverviewPage() {
  const { data: userData, isLoading: isUserLoading } = useUser();

  const userId = userData?._id;

  const { data: dashboardData , isLoading: isDashboardLoading } = useClientDashboard(userId, { enabled: !!userId });

  console.log("Dashboard Data:", dashboardData);

  if (isUserLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
       <Loader />
      </div>
    );
  }

  if (!userData || !userId) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-lg">Failed to load user data</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-accent text-white rounded-lg cursor-pointer"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (isDashboardLoading) {
    return (
      <div>
        <TitleHeaderDashboard 
          title="Overview" 
          subtitle="Welcome to your dashboard overview"
        />
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader />
        </div>
      </div>
    );
  }

  const totals = dashboardData?.totals || {};
  const ordersByStatus = dashboardData?.ordersByStatus || {};
  const recentOrders = Array.isArray(dashboardData?.orders) ? dashboardData.orders : [];
  const reviews = Array.isArray(dashboardData?.reviews) ? dashboardData.reviews : [];

  const getStatusColor = (status) => {
    switch ((status || "").toLowerCase()) {
      case "delivered":
      case "completed":
        return "bg-green-100 text-green-700";
      case "pending":
        return "bg-yellow-100 text-yellow-700";
      case "processing":
        return "bg-blue-100 text-blue-700";
      case "canceled":
      case "cancelled":
        return "bg-red-100 text-red-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div>
      <TitleHeaderDashboard 
        title="Overview" 
        subtitle="Welcome to your dashboard overview"
      />

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 px-10 mt-8">
        <Card
          title="Total Orders"
          amount={totals.orders || 0}
          icon={<FaShoppingCart className="text-accent" size={20} />}
        />
        <Card
          title="Delivered"
          amount={ordersByStatus.completed || 0}
          icon={<FaCheckCircle className="text-accent" size={20} />}
        />
        <Card
          title="Pending"
          amount={ordersByStatus.pending || 0}
          icon={<FaClock className="text-accent" size={20} />}
        />
        <Card
          title="Canceled"
          amount={(ordersByStatus.canceled || 0) + (ordersByStatus.cancelled || 0)}

          icon={<FaTimesCircle className="text-accent" size={20} />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 px-10 mt-8 mb-10">

        <div className="lg:col-span-2 bg-white rounded-2xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-800">Recent Orders</h2>
            <Link to="/client/dashboard/orders" className="text-accent hover:text-accent-hover text-sm font-medium transition-colors cursor-pointer">
              View All
            </Link>
          </div>

          <div className="space-y-4">
            {recentOrders.map((order) => (
              <div
                key={order._id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800">{order._id}</h3>
                  <p className="text-sm text-gray-500">{dayjs(order.createdAt).fromNow()}</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="font-semibold text-gray-800">${Number(order.total || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    <p className="text-sm text-gray-500">{Array.isArray(order.items) ? order.items.length : 0} items</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                      order.status
                    )}`}
                  >
                    {order.status}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {recentOrders.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <FaShoppingCart size={48} className="mx-auto mb-4 opacity-50" />
              <p>No orders yet</p>
            </div>
          )}
        </div>

        {/* Reviews Section - Takes 1 column */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-800">Reviews</h2>
            <FaStar className="text-yellow-500" size={20} />
          </div>

          <div className="space-y-4">
            {/* Review Item 1 */}
            {reviews.map((review, index) => (
              <div key={index} className="p-4 bg-purple-50 rounded-lg border border-purple-100">
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex">
                    {[1,2,3,4,5].map((star) => (
                      <p key={star}
                        className="my-1"
                        ><FaStar className={review.rating >= star ? "text-yellow-500" : "text-gray-300"}/>
                      </p>
                    ))} 
                  </div>
                  <span className="text-xs text-gray-500">{dayjs(review.createdAt).fromNow()}</span>
                </div>
                <p className="text-sm text-gray-700">
                  {review.comment}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}