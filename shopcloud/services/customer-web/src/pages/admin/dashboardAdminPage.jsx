import { MdOutlineAttachMoney } from "react-icons/md";
import { TiShoppingCart } from "react-icons/ti";
import { SiDropbox } from "react-icons/si";
import { BsExclamationTriangle } from "react-icons/bs";
import TitleHeaderDashboard from "../../components/TitleHeader";
import { useEffect, useState } from "react";
import { fetchDashboardOverview } from "../../services/dashboardService";
import { useNavigate } from "react-router-dom";

export default function DashboardAdminPage() {
  const [overview, setOverview] = useState(null);
  const navigate = useNavigate();
  const totals = overview?.totals || {};
  const needsAttention = overview?.needsAttention || {};
  const recentOrders = overview?.recentOrders || [];
  const lowStockTable = overview?.lowStockTable || [];
  const cardClass = "bg-white rounded-2xl shadow p-4 border border-gray-100";

  useEffect(() => {
    const dashboardData =  async () => {
      try {
        const response = await fetchDashboardOverview();
        setOverview(response);
        console.log("Dashboard overview data:", response);
      } catch (error) {
        console.error("Error fetching dashboard overview:", error);
      }
    } 
    dashboardData();
  }, [])
  return (
    <div className="w-full h-full">
      <TitleHeaderDashboard title="Dashboard Overview" subtitle="Welcome back to ShopCloud Admin." />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 w-full mb-6">
        <div className={cardClass}>
          <p className="text-sm text-gray-500">Revenue This Month</p>
          <div className="flex items-center justify-between mt-2">
            <p className="text-2xl font-bold">${Number(totals.revenueThisMonth || 0).toFixed(2)}</p>
            <MdOutlineAttachMoney className="text-accent text-2xl" />
          </div>
        </div>
        <div className={cardClass}>
          <p className="text-sm text-gray-500">Pending Orders</p>
          <div className="flex items-center justify-between mt-2">
            <p className="text-2xl font-bold">{totals.pendingOrders ?? 0}</p>
            <TiShoppingCart className="text-accent text-2xl" />
          </div>
        </div>
        <div className={cardClass}>
          <p className="text-sm text-gray-500">Low Stock Products</p>
          <div className="flex items-center justify-between mt-2">
            <p className="text-2xl font-bold">{totals.lowStockProducts ?? 0}</p>
            <BsExclamationTriangle className="text-accent text-2xl" />
          </div>
        </div>
        <div className={cardClass}>
          <p className="text-sm text-gray-500">Total Products</p>
          <div className="flex items-center justify-between mt-2">
            <p className="text-2xl font-bold">{totals.products ?? 0}</p>
            <SiDropbox className="text-accent text-2xl" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 mb-6">
        <div className={cardClass}>
          <h3 className="text-lg font-semibold mb-3">Quick Actions</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button className="bg-accent text-white py-2 rounded-lg hover:bg-accent-hover" onClick={() => navigate("/admin/newProduct")}>Add Product</button>
            <button className="bg-accent text-white py-2 rounded-lg hover:bg-accent-hover" onClick={() => navigate("/admin/orders")}>View Orders</button>
            <button className="bg-accent text-white py-2 rounded-lg hover:bg-accent-hover" onClick={() => navigate("/admin/products")}>Manage Inventory</button>
            <button className="bg-accent text-white py-2 rounded-lg hover:bg-accent-hover" onClick={() => navigate("/admin/categories")}>Add Category</button>
          </div>
        </div>
        <div className={cardClass}>
          <h3 className="text-lg font-semibold mb-3">Needs Attention</h3>
          <ul className="space-y-2 text-sm">
            <li className="flex justify-between"><span>Low-stock products</span><span className="font-semibold">{needsAttention.lowStockProducts ?? 0}</span></li>
            <li className="flex justify-between"><span>Pending orders</span><span className="font-semibold">{needsAttention.pendingOrders ?? 0}</span></li>
            <li className="flex justify-between"><span>Products missing images</span><span className="font-semibold">{needsAttention.productsMissingImages ?? 0}</span></li>
            <li className="flex justify-between"><span>Pending reviews</span><span className="font-semibold">{needsAttention.pendingReviews ?? 0}</span></li>
            <li className="flex justify-between"><span>Pending return requests</span><span className="font-semibold">{needsAttention.pendingReturnRequests ?? 0}</span></li>
          </ul>
        </div>
      </div>

      <div className={cardClass + " mb-6 overflow-auto"}>
        <h3 className="text-lg font-semibold mb-3">Recent Orders</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Order ID</th>
              <th className="text-left py-2">Customer</th>
              <th className="text-left py-2">Total</th>
              <th className="text-left py-2">Status</th>
              <th className="text-left py-2">Date</th>
              <th className="text-left py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {recentOrders.map((order) => (
              <tr key={order._id} className="border-b">
                <td className="py-2">{order._id}</td>
                <td className="py-2">{order.customerName}</td>
                <td className="py-2">${Number(order.total || 0).toFixed(2)}</td>
                <td className="py-2 capitalize">{order.status}</td>
                <td className="py-2">{order.createdAt ? new Date(order.createdAt).toLocaleString() : "-"}</td>
                <td className="py-2">
                  <button className="text-white bg-accent px-3 py-1 rounded-md hover:bg-accent-hover" onClick={() => navigate("/admin/orders")}>View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className={cardClass + " overflow-auto"}>
        <h3 className="text-lg font-semibold mb-3">Low Stock Products</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Product Name</th>
              <th className="text-left py-2">Category</th>
              <th className="text-left py-2">Stock</th>
              <th className="text-left py-2">Status</th>
              <th className="text-left py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {lowStockTable.map((row) => (
              <tr key={row._id} className="border-b">
                <td className="py-2">{row.name}</td>
                <td className="py-2">{row.category}</td>
                <td className="py-2">{row.stock}</td>
                <td className="py-2">{row.status}</td>
                <td className="py-2">
                  <button className="text-white bg-accent px-3 py-1 rounded-md hover:bg-accent-hover" onClick={() => navigate("/admin/products")}>Edit / Restock</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}