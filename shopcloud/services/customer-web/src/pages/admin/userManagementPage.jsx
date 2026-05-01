import { useEffect, useState } from 'react';
import { FaSearch, FaCheckCircle } from 'react-icons/fa';
import TitleHeaderDashboard from '../../components/TitleHeader';
import axios from 'axios';
import { optionalBearerHeaders } from '../../config/axiosConfig';
import { publicApiOrigin } from '../../utils/publicApiOrigin';
import toast from 'react-hot-toast';

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [selectedDetails, setSelectedDetails] = useState(null);


  useEffect(() => {

    axios.get(`${publicApiOrigin()}/api/users`,{
      headers: optionalBearerHeaders(),
      withCredentials: true,
    }).then((res) => {
      console.log(res.data.users);
      setUsers(res.data.users);

    }).catch((err) => {
      console.log("Error Fetching user", err);
    });

  },[])
 

  const handleBlockToggle = (userId) => {
    axios.put(`${publicApiOrigin()}/api/users/`+userId+"/block", {}, {
      headers: optionalBearerHeaders(),
      withCredentials: true,
    }).then(() => {
      setUsers(prevUsers => prevUsers.map(user => 
        user._id === userId ? {...user, isBlocked: !user.isBlocked} : user
      ));
      toast.success("User status updated");

    }).catch((err) => {
      console.error(err);
      toast.error("fail");
    })
      
  };

  const loadUserDetails = async (userId) => {
    try {
      const res = await axios.get(`${publicApiOrigin()}/api/users/` + userId + "/details", {
        headers: optionalBearerHeaders(),
        withCredentials: true,
      });
      setSelectedDetails(res.data);
    } catch (err) {
      console.error(err);
      toast.error("Failed to load user details");
    }
  };

  const filteredUsers = users.filter(user => {
    const displayName = user.name || "";
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          displayName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || 
                          (filterStatus === 'active' && !user.isBlocked) ||
                          (filterStatus === 'blocked' && user.isBlocked);
    return matchesSearch && matchesFilter;
  });

  const totalUsers = users.length;
  const activeUsers = users.filter(u => !u.isBlocked).length;
  const blockedUsers = users.filter(u => u.isBlocked).length;

  return (
    <div>

      <TitleHeaderDashboard title="User Management" subtitle="Manage and monitor all user accounts" />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-white flex items-center p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="relative w-full">
            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-accent" size={20} />
            <input 
              className="w-full pl-10 pr-4 py-2 border border-accent rounded-lg placeholder:text-accent focus:outline-none focus:ring-2 focus:ring-accent-hover"
              placeholder="Search by name or email"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <div className="text-sm text-gray-600 mb-1">Total Users</div>
            <div className="text-2xl font-bold text-blue-600">{totalUsers}</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <div className="text-sm text-gray-600 mb-1">Active</div>
            <div className="text-2xl font-bold text-green-600">{activeUsers}</div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg border border-red-200">
            <div className="text-sm text-gray-600 mb-1">Blocked</div>
            <div className="text-2xl font-bold text-red-600">{blockedUsers}</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-4 p-4">
        <div className="flex gap-2 ">
          <button 
            onClick={() => setFilterStatus('all')}
            className={`px-4 py-2 rounded-lg cursor-pointer ${filterStatus === 'all' ? 'bg-accent text-white' : 'bg-gray-100 text-gray-700'}`}>
            All Users
          </button>
          <button 
            onClick={() => setFilterStatus('active')}
            className={`px-4 py-2 rounded-lg cursor-pointer ${filterStatus === 'active' ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-700'}`}>
            Active
          </button>
          <button 
            onClick={() => setFilterStatus('blocked')}
            className={`px-4 py-2 rounded-lg cursor-pointer ${filterStatus === 'blocked' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-700'}`}>
            Blocked
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="h-[500px] overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">User</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Email</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Join Date</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Verification</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Orders</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
              </tr>  
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user._id} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2"> 
                        <img src={user.image || "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='80' height='80'><rect width='100%25' height='100%25' fill='%23f3f4f6'/></svg>"} alt={user.name} className="w-10 h-10 rounded-full object-cover" />
                        <h2>{user.name || "User"}</h2>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-gray-600">{user.email}</td>
                  <td className="px-4 py-4 text-gray-600">{new Date(user.createdAt).toLocaleDateString()}</td>
                  <td className="px-4 py-4">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full gap-1 ${
                      !user.isBlocked ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {!user.isBlocked ? <><FaCheckCircle /> Active</> : 'Blocked'}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-gray-600">-</td>
                  <td className="px-4 py-4">
                    <div className="flex gap-2">
                      <button 
                        onClick={() => loadUserDetails(user._id)}
                        className="px-4 py-1 rounded-lg text-sm font-medium cursor-pointer bg-blue-500 text-white hover:bg-blue-600"
                      >
                        Details
                      </button>
                      <button 
                        onClick={() => handleBlockToggle(user._id)}
                        className={`px-4 py-1 rounded-lg text-sm font-medium cursor-pointer ${
                        user.isBlocked 
                          ? 'bg-green-500 text-white hover:bg-green-600' 
                          : 'bg-red-500 text-white hover:bg-red-600'
                        }`}>
                        {user.isBlocked ? 'Unblock' : 'Block'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredUsers.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No users found matching your criteria
          </div>
        )}
      </div>
      {selectedDetails && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white w-[760px] max-h-[80vh] overflow-y-auto rounded-xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">Customer Details</h3>
              <button className="text-red-600" onClick={() => setSelectedDetails(null)}>Close</button>
            </div>
            <p className="mb-1"><strong>Name:</strong> {selectedDetails.user?.name || "User"}</p>
            <p className="mb-1"><strong>Email:</strong> {selectedDetails.user?.email || "-"}</p>
            <p className="mb-4"><strong>Role:</strong> {selectedDetails.user?.role || "-"}</p>

            <h4 className="font-semibold mb-2">Order History</h4>
            <table className="w-full text-sm mb-4">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-1">Order ID</th>
                  <th className="text-left py-1">Status</th>
                  <th className="text-left py-1">Total</th>
                  <th className="text-left py-1">Created</th>
                </tr>
              </thead>
              <tbody>
                {(selectedDetails.orders || []).map((order) => (
                  <tr key={order._id} className="border-b">
                    <td className="py-1">{order._id}</td>
                    <td className="py-1">{order.status}</td>
                    <td className="py-1">${Number(order.total || 0).toFixed(2)}</td>
                    <td className="py-1">{order.createdAt ? new Date(order.createdAt).toLocaleString() : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h4 className="font-semibold mb-2">Return Requests</h4>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-1">Return ID</th>
                  <th className="text-left py-1">Order ID</th>
                  <th className="text-left py-1">Status</th>
                  <th className="text-left py-1">Reason</th>
                </tr>
              </thead>
              <tbody>
                {(selectedDetails.returns || []).map((ret) => (
                  <tr key={ret._id} className="border-b">
                    <td className="py-1">{ret._id}</td>
                    <td className="py-1">{ret.orderId}</td>
                    <td className="py-1">{ret.status}</td>
                    <td className="py-1">{ret.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}