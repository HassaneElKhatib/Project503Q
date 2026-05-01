import axios from "axios";
import { optionalBearerHeaders } from "../../config/axiosConfig";
import { publicApiOrigin } from "../../utils/publicApiOrigin";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import TitleHeaderDashboard from "../../components/TitleHeader";

export default function OrdersAdminPage() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [returns, setReturns] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  async function loadData() {
    try {
      setIsLoading(true);
      const [ordersRes, returnsRes] = await Promise.all([
        axios.get(`${publicApiOrigin()}/api/orders`, {
          headers: optionalBearerHeaders(),
          withCredentials: true,
        }),
        axios.get(`${publicApiOrigin()}/api/orders/returns`, {
          headers: optionalBearerHeaders(),
          withCredentials: true,
        }),
      ]);
      setOrders(ordersRes.data.orders || []);
      setReturns(returnsRes.data.returns || []);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load admin orders");
      if (error.response?.status === 401) {
        navigate("/admin/login");
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function updateOrderStatus(orderId, status) {
    try {
      await axios.put(
        `${publicApiOrigin()}/api/orders/${orderId}`,
        { status },
        { headers: optionalBearerHeaders(), withCredentials: true }
      );
      toast.success("Order status updated");
      loadData();
    } catch (error) {
      console.error(error);
      toast.error("Failed to update order");
    }
  }

  async function updateReturnStatus(returnId, status) {
    try {
      await axios.put(
        `${publicApiOrigin()}/api/orders/returns/${returnId}`,
        { status },
        { headers: optionalBearerHeaders(), withCredentials: true }
      );
      toast.success("Return status updated");
      loadData();
    } catch (error) {
      console.error(error);
      toast.error("Failed to update return");
    }
  }

  return (
    <div className="w-full h-full flex flex-col gap-6">
      <TitleHeaderDashboard title="Orders Management" subtitle="Manage customer orders and return requests." />

      {isLoading ? (
        <div className="p-8 bg-white rounded-xl shadow">Loading...</div>
      ) : (
        <>
          <div className="bg-white rounded-xl shadow p-4 overflow-auto">
            <h2 className="font-semibold text-xl mb-3">Orders</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Order</th>
                  <th className="text-left py-2">Status</th>
                  <th className="text-left py-2">Total</th>
                  <th className="text-left py-2">Created</th>
                  <th className="text-left py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order._id} className="border-b">
                    <td className="py-2">{order._id}</td>
                    <td className="py-2">{order.status}</td>
                    <td className="py-2">${Number(order.total || 0).toFixed(2)}</td>
                    <td className="py-2">{order.createdAt ? new Date(order.createdAt).toLocaleString() : "-"}</td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <button className="px-2 py-1 rounded bg-yellow-500 text-white" onClick={() => updateOrderStatus(order._id, "pending")}>Pending</button>
                        <button className="px-2 py-1 rounded bg-indigo-600 text-white" onClick={() => updateOrderStatus(order._id, "processing")}>Processing</button>
                        <button className="px-2 py-1 rounded bg-blue-600 text-white" onClick={() => updateOrderStatus(order._id, "shipped")}>Shipped</button>
                        <button className="px-2 py-1 rounded bg-green-600 text-white" onClick={() => updateOrderStatus(order._id, "delivered")}>Delivered</button>
                        <button className="px-2 py-1 rounded bg-red-600 text-white" onClick={() => updateOrderStatus(order._id, "cancelled")}>Cancel</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-white rounded-xl shadow p-4 overflow-auto">
            <h2 className="font-semibold text-xl mb-3">Return Requests</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Return ID</th>
                  <th className="text-left py-2">Order ID</th>
                  <th className="text-left py-2">Reason</th>
                  <th className="text-left py-2">Status</th>
                  <th className="text-left py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {returns.map((ret) => (
                  <tr key={ret._id} className="border-b">
                    <td className="py-2">{ret._id}</td>
                    <td className="py-2">{ret.orderId}</td>
                    <td className="py-2">{ret.reason}</td>
                    <td className="py-2">{ret.status}</td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <button className="px-2 py-1 rounded bg-green-600 text-white" onClick={() => updateReturnStatus(ret._id, "approved")}>Approve</button>
                        <button className="px-2 py-1 rounded bg-red-600 text-white" onClick={() => updateReturnStatus(ret._id, "rejected")}>Reject</button>
                        <button className="px-2 py-1 rounded bg-blue-600 text-white" onClick={() => updateReturnStatus(ret._id, "received")}>Received</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}