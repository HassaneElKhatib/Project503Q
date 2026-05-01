import { ImPlus } from "react-icons/im";
import { Link, useNavigate } from "react-router-dom";
import { FaTrashCan } from "react-icons/fa6";
import { useEffect, useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";
import { FaRegEdit } from "react-icons/fa";
import Loader from "../../components/loader";
import TitleHeaderDashboard from "../../components/TitleHeader";

export default function ProductsAdminPage() {
  const[products, setProducts] = useState([]);
  const[isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const FALLBACK_IMAGE = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='80' height='80'><rect width='100%25' height='100%25' fill='%23f3f4f6'/></svg>";

  const normalizeProduct = (product) => {
    const imageUrl = product.image_url || product.imageUrl;
    const rawPrice = product.price ?? product.price_cents ?? 0;
    const normalizedPrice = Number(product.price_cents != null ? Number(rawPrice) / 100 : rawPrice);
    return {
      ...product,
      productId: product.productId ?? product.id ?? product.sku ?? "",
      images: Array.isArray(product.images) ? product.images : (imageUrl ? [imageUrl] : []),
      price: normalizedPrice,
      labelledPrice: Number(product.labelledPrice ?? product.lastPrice ?? normalizedPrice),
      stock: Number(product.stock ?? 0),
      isActive: product.isActive !== false,
    };
  };

  useEffect(
      () => {
      if(isLoading){
        axios.get(import.meta.env.VITE_BACKEND_URL+"/api/products/admin",{
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`
          }
        }
        ).then(
          (res) => {
            console.log(res.data);
            const rawProducts = res.data?.products ?? res.data?.items ?? [];
            setProducts(Array.isArray(rawProducts) ? rawProducts.map(normalizeProduct) : []);
            setIsLoading(false);
          }
          )
      }
    },
    [isLoading]
  )
  const navigate = useNavigate();
  const categories = Array.from(new Set(products.map((product) => product.category).filter(Boolean)));
  const filteredProducts = products.filter((product) => {
    const searchLower = search.trim().toLowerCase();
    const matchesSearch = !searchLower || (product.name || "").toLowerCase().includes(searchLower);
    const matchesCategory = categoryFilter === "all" || product.category === categoryFilter;
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && product.isActive) ||
      (statusFilter === "inactive" && !product.isActive);
    return matchesSearch && matchesCategory && matchesStatus;
  });
  
  return (
    <div className="w-full h-full">

      <TitleHeaderDashboard title="Products Management" subtitle="Manage all the products available in the store." />

      {isLoading?<Loader /> 
      : (<>
      <div className="bg-white rounded-xl p-3 mb-3 flex gap-3 items-center">
        <input
          className="border border-gray-300 px-3 py-2 rounded-md w-[280px]"
          placeholder="Search products by name"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="border border-gray-300 px-3 py-2 rounded-md" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          <option value="all">All categories</option>
          {categories.map((category) => <option key={category} value={category}>{category}</option>)}
        </select>
        <select className="border border-gray-300 px-3 py-2 rounded-md" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
      <table className="w-full bg-white text-left">
        <thead className="bg-gray-200">
          <tr>
            <th className="p-2 border border-gray-300">Image</th>
            <th className="p-2 border border-gray-300">Product Id</th>
            <th className="p-2 border border-gray-300">Name</th>
            <th className="p-2 border border-gray-300">Description</th>
            <th className="p-2 border border-gray-300">Price</th>
            <th className="p-2 border border-gray-300">Labelled Price</th>
            <th className="p-2 border border-gray-300">Stock</th>
            <th className="p-2 border border-gray-300">Category</th>
            <th className="p-2 border border-gray-300">Status</th>
            <th className="p-2 border border-gray-300">Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredProducts.map((product, index) => (
            <tr key={index} className="hover:bg-gray-100">
              <td className="p-2 border border-gray-300">
                <img
                  src={product.images[0] || FALLBACK_IMAGE}
                  alt={product.name}
                  className="w-12 h-12"
                />
              </td>
              <td className="p-2 border border-gray-300">{product.productId}</td>
              <td className="p-2 border border-gray-300">{product.name}</td>
              <td className="p-2 border border-gray-300 max-w-[200px] truncate">
                {product.description}
              </td>
              <td className="p-2 border border-gray-300">{product.price}</td>
              <td className="p-2 border border-gray-300">{product.labelledPrice}</td>
              <td className="p-2 border border-gray-300">{product.stock}</td>
              <td className="p-2 border border-gray-300">{product.category}</td>
              <td className="p-2 border border-gray-300">{product.isActive ? "Active" : "Inactive"}</td>
              <td className="p-4 border border-gray-300 flex justify-center items-center gap-2">
                <button
                  className="text-white bg-emerald-600 px-2 py-1 rounded hover:bg-emerald-700"
                  onClick={async () => {
                    const token = localStorage.getItem("token");
                    await axios.put(
                      import.meta.env.VITE_BACKEND_URL + "/api/products/" + product.productId + "/stock",
                      { delta: 1 },
                      { headers: { Authorization: `Bearer ${token}` } }
                    );
                    setIsLoading(true);
                  }}
                >
                  +1 Stock
                </button>
                <button
                  className="text-white bg-orange-600 px-2 py-1 rounded hover:bg-orange-700"
                  onClick={async () => {
                    const token = localStorage.getItem("token");
                    await axios.put(
                      import.meta.env.VITE_BACKEND_URL + "/api/products/" + product.productId + "/stock",
                      { delta: -1 },
                      { headers: { Authorization: `Bearer ${token}` } }
                    );
                    setIsLoading(true);
                  }}
                >
                  -1 Stock
                </button>
                <button className="text-white bg-red-600 p-[10px] rounded-full hover:text-red-800"
                onClick={
                  ()=> {
                    const tocken = localStorage.getItem("token");
                    if(!tocken){
                      navigate("/login");
                      return;
                    }

                    axios.delete(import.meta.env.VITE_BACKEND_URL+"/api/products/" + product.productId,
                    {
                      headers:{
                        Authorization: `Bearer ${tocken}`
                      }
                    }).then(
                      (res) => {
                        console.log("Product Disabled Successfully");
                        console.log(res.data);
                        toast.success("Product disabled successfully");
                        setIsLoading(!isLoading);

                      }
                    ).catch(
                      (err) => {
                        console.error("Error Deleting Product:", err);
                        toast.error("Failed to delete product. Please try again.");
                      }
                    )
                  }
                }>
                  <FaTrashCan />
                </button>
                <button className="text-white bg-blue-500 p-[10px] rounded-full hover:text-blue-800"
                  onClick={
                    () => {
                      navigate("/admin/updateProduct", {
                        state: product
                      });
                    }
                  }
                >
                  <FaRegEdit />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </>)
      }
      <Link
        to={"/admin/newProduct"}
        className="fixed right-[60px] bottom-[60px] p-[20px] rounded-full text-white bg-black shadow-2xl cursor-pointer"
      >
        <ImPlus className="text-2xl" />
      </Link>
    </div>
  );
}
