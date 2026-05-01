import { useLocation, useNavigate } from "react-router-dom";

export default function OrderConfirmationPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const order = location.state?.order;
  const invoice = location.state?.invoice;

  if (!order) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center bg-primary">
        <div className="bg-white p-8 rounded-xl shadow-xl text-center">
          <h1 className="text-2xl font-bold mb-3">No order found</h1>
          <p className="text-gray-600 mb-5">Place an order first to view confirmation.</p>
          <button
            className="px-5 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover"
            onClick={() => navigate("/products")}
          >
            Back to products
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen flex items-center justify-center bg-primary px-4">
      <div className="w-full max-w-2xl bg-white p-8 rounded-xl shadow-xl">
        <h1 className="text-3xl font-bold text-green-600 mb-2">Order confirmed</h1>
        <p className="text-gray-700 mb-6">Your order has been placed successfully.</p>

        <div className="space-y-2 text-sm">
          <p><b>Order ID:</b> {order._id}</p>
          <p><b>Status:</b> {order.status}</p>
          <p><b>Total:</b> ${Number(order.total || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
          <p><b>Items:</b> {Array.isArray(order.items) ? order.items.length : 0}</p>
          <p><b>Invoice ID:</b> {invoice?.invoiceId || "N/A"}</p>
          <p><b>Invoice Email Queue:</b> {invoice?.emailQueued ? "Queued" : "N/A"}</p>
        </div>

        <div className="flex gap-3 mt-8">
          <button
            className="px-5 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover"
            onClick={() => navigate("/orders")}
          >
            View my orders
          </button>
          <button
            className="px-5 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
            onClick={() => navigate("/products")}
          >
            Continue shopping
          </button>
        </div>
      </div>
    </div>
  );
}
