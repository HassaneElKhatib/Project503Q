import axios from "axios";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";

export default function AddProductAdminPage() {
  const navigate = useNavigate();

  const [productName, setProductName] = useState("");
  const [alternativeNames, setAlternativeNames] = useState("");
  const [labelledPrice, setLabelledPrice] = useState("");
  const [price, setPrice] = useState("");
  const [description, setDescription] = useState("");
  const [stock, setStock] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [category, setCategory] = useState("general");
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    axios
      .get(import.meta.env.VITE_BACKEND_URL + "/api/categories", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      })
      .then((res) => setCategories(res.data.categories || []))
      .catch(() => setCategories([]));
  }, []);

  async function handleSubmit() {
    setIsLoading(true);

    try {
      const token = localStorage.getItem("token");

      if (!token) {
        navigate("/login");
        return;
      }

      const imageUrls = [];

      const alternativeArray = alternativeNames.split(",").map(name => name.trim()).filter(Boolean);

      const productData = {
        name: productName,
        altNames: alternativeArray,
        lastPrice: Number(labelledPrice),
        price: Number(price),
        images: imageUrls,
        description,
        stock: Number(stock),
        isActive,
        category,
      };

      const res = await axios.post(
        import.meta.env.VITE_BACKEND_URL + "/api/products",
        productData,
        {
          headers: {
            Authorization: "Bearer " + token
          }
        }
      );

      console.log("Product Was Successfully Created");
      console.log(res.data);
      toast.success("Product created successfully!");
      navigate("/admin/products");
    } catch (err) {
      console.error("Error creating product:", err);
      toast.error("Failed to create product. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="w-full min-h-screen flex justify-center items-center p-4">
      <div className="w-full max-w-2xl bg-white border border-gray-200 rounded-lg shadow-sm p-8">
        <h1 className="text-2xl font-bold mb-6 text-gray-900">Add Product</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Product Name</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              className="w-full border border-gray-300 h-10 rounded-md px-3 focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>

          <div className="md:col-span-2 flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Alternative Names</label>
            <input
              type="text"
              value={alternativeNames}
              onChange={(e) => setAlternativeNames(e.target.value)}
              placeholder="Separate with commas"
              className="w-full border border-gray-300 h-10 rounded-md px-3 focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Labelled Price</label>
            <input
              type="number"
              value={labelledPrice}
              onChange={(e) => setLabelledPrice(e.target.value)}
              className="w-full border border-gray-300 h-10 rounded-md px-3 focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Price</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full border border-gray-300 h-10 rounded-md px-3 focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>

          <div className="md:col-span-2 flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Images (disabled for now)</label>
            <input
              type="file"
              multiple
              accept="image/*"
              disabled
              className="w-full border border-gray-300 rounded-md px-3 py-2 file:mr-4 file:py-1 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-accent hover:file:bg-blue-100"
            />
          </div>

          <div className="md:col-span-2 flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full border border-gray-300 h-24 rounded-md px-3 py-2 focus:ring-2 focus:ring-accent focus:border-transparent resize-none"
            ></textarea>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Stock</label>
            <input
              type="number"
              value={stock}
              onChange={(e) => setStock(e.target.value)}
              className="w-full border border-gray-300 h-10 rounded-md px-3 focus:ring-2 focus:ring-accent focus:border-transparent"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Availability</label>
            <select
              value={isActive}
              onChange={(e) => setIsActive(e.target.value === "true")}
              className="w-full border border-gray-300 h-10 rounded-md px-3 focus:ring-2 focus:ring-accent focus:border-transparent"
            >
              <option value={true}>Available</option>
              <option value={false}>Not Available</option>
            </select>
          </div>

          <div className="md:col-span-2 flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full border border-gray-300 h-10 rounded-md px-3 focus:ring-2 focus:ring-accent focus:border-transparent"
            >
              {categories.length === 0 ? (
                <>
                  <option value="general">General</option>
                  <option value="electronics">Electronics</option>
                  <option value="fashion">Fashion</option>
                  <option value="home">Home Essentials</option>
                </>
              ) : (
                categories.map((cat) => (
                  <option key={cat._id} value={cat.name}>{cat.name}</option>
                ))
              )}
            </select>
          </div>
        </div>

        <div className="flex gap-4 mt-8 justify-end">
          <Link
            to="/admin/products"
            className="px-6 py-2.5 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors font-medium"
          >
            Cancel
          </Link>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="px-6 py-2.5 bg-accent text-white rounded-md hover:bg-accent-hover transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed cursor-pointer"
          >
            {isLoading ? "Adding..." : "Add Product"}
          </button>
        </div>
      </div>
    </div>
  );
}
