import { Link, Route, Routes, useNavigate } from "react-router-dom";
import { HiShoppingBag } from "react-icons/hi2";
import { GiLipstick } from "react-icons/gi";
import { ImUsers } from "react-icons/im";
import { IoSettings } from "react-icons/io5";
import ProductsAdminPage from "./admin/productsAdminPage";
import AddProductAdminPage from "./admin/addProductAdminPage";
import UpdateProductPage from "./admin/updateProductPage";
import OrdersAdminPage from "./admin/ordersAdminPage";
import UserManagementPage from "./admin/userManagementPage";
import SettingAdminPage from "./admin/settingAdminPage";
import { MdDashboard } from "react-icons/md";
import DashboardAdminPage from "./admin/dashboardAdminPage";
import { useEffect, useRef, useState } from "react";
import { getUserById } from "../services/userService";
import toast from "react-hot-toast";
import useLogout from "../utils/logout";
import { FaStar } from "react-icons/fa6";
import ReviewsManagementPage from "./admin/reviewsManagementPage";
import { MdCategory } from "react-icons/md";
import CategoriesAdminPage from "./admin/categoriesAdminPage";

export default function AdminPage() {
  const navigate = useNavigate();
  const [admin, setAdmin] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const hasWelcomed = useRef(false);

  const logout = useLogout();
  const adminDisplayName = admin?.firstName || admin?.name || "Admin";

  useEffect(() => {
    const fetchAdminData = async () => {
      if (!isLoading) return;
      const token = localStorage.getItem("token");
      if (!token) {
        toast.error("Please login as admin");
        navigate("/admin/login");
        return;
      }
      try {
        const response = await getUserById();
        console.log(response);
        setAdmin(response);

        if (response.role !== "admin") {
          toast.error("Unotherized acess. Admins only");
          navigate("/admin/login");
          return;
        }

        if (!hasWelcomed.current) {
          toast.success(`Welcome back, ${response.firstName || response.name || "Admin"}`);
          hasWelcomed.current = true;
        }
        
      }catch(err) {
        toast.error("Faild to fetch admin data");
        console.log("error", err);
      }
    
      setIsLoading(false);
    }
    fetchAdminData();
  }, [isLoading, navigate]);

  return(
    <div className="w-screen h-full flex m-0 p-0">
      <div className="w-[280px] min-h-screen flex flex-col items-center shadow-xl">
          <span className="text-3xl font-bold my-5"> Admin Panel </span>
          <Link className="flex flex-row h-[60px] w-full p-[20px] items-center text-xl gap-[25px] hover:bg-accent hover:text-white" to="/admin"> <MdDashboard /> Dashboard </Link>
          <Link className="flex flex-row h-[60px] w-full p-[20px] items-center text-xl gap-[25px] hover:bg-accent hover:text-white" to="/admin/products"> <GiLipstick /> Products </Link>
          <Link className="flex flex-row h-[60px] w-full p-[20px] items-center text-xl gap-[25px] hover:bg-accent hover:text-white" to="/admin/orders"> <HiShoppingBag /> Orders </Link>
          <Link className="flex flex-row h-[60px] w-full p-[20px] items-center text-xl gap-[25px] hover:bg-accent hover:text-white" to="/admin/categories"> <MdCategory /> Categories </Link>
          <Link className="flex flex-row h-[60px] w-full p-[20px] items-center text-xl gap-[25px] hover:bg-accent hover:text-white" to="/admin/reviews"> <FaStar /> Reviews </Link>
          <Link className="flex flex-row h-[60px] w-full p-[20px] items-center text-xl gap-[25px] hover:bg-accent hover:text-white" to="/admin/users"> <ImUsers /> Users </Link>
          <Link className="flex flex-row h-[60px] w-full p-[20px] items-center text-xl gap-[25px] hover:bg-accent hover:text-white" to="/admin/settings"> <IoSettings /> Settings </Link>
      </div>
      <div className="w-[calc(100%-300px)] h-full pl-10 pr-5 pt-3 pb-7">
        <div className="h-15 flex justify-end items-center mb-2">
          <div className="flex items-center gap-2">
            <img src={admin?.image || undefined} className="w-10 h-10 rounded-full object-cover" alt="Admin Profile Picture">
            </img>
            <h2 className="text-lg font-mono">{adminDisplayName}</h2>
            <button className="bg-accent py-1 px-3 font-serif rounded-2xl ml-3 hover:bg-accent-hover items-center justify-center shadow-lg border-2 text-lg border-accent cursor-pointer" 
            onClick={logout}
            >
            Logout
          </button>
          </div>
        </div>
        <Routes path="/">
          <Route path="/" element={<DashboardAdminPage />}/>
          <Route path="/products" element={<ProductsAdminPage />}/>
          <Route path="/newProduct" element={<AddProductAdminPage />}/>
          <Route path="/orders" element={<OrdersAdminPage />}/>
          <Route path="/categories" element={<CategoriesAdminPage />}/>
          <Route path="/updateProduct" element={<UpdateProductPage />}/>
          <Route path="/reviews" element={<ReviewsManagementPage />}/>
          <Route path="/users" element={<UserManagementPage />}/>
          <Route path="/settings" element={<SettingAdminPage />}/>
        </Routes>
        </div>
    </div>
  )
}