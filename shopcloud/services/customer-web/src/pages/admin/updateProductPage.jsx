import axios from "axios";
import { optionalBearerHeaders } from "../../config/axiosConfig";
import { publicApiOrigin } from "../../utils/publicApiOrigin";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useLocation, useNavigate } from "react-router-dom";

export default function UpdateProductPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const product = location.state || null;
  useEffect(() => {
    if (!product) {
      toast.error("Missing product data. Open update from products table.");
      navigate("/admin/products");
    }
  }, [product, navigate]);
  
  const [productId] = useState(product?.productId || product?._id || product?.id || "");
  const [productName, setProductName] = useState(product?.name || "");
  const [alternativeNames, setAlternativeNames] = useState((product?.altNames || []).join(","));
  const [labelledPrice, setLabelledPrice] = useState(product?.labelledPrice ?? product?.lastPrice ?? product?.price ?? 0);
  const [price, setPrice] = useState(product?.price ?? 0);
  const [images, setImages] = useState([]);
  const [description, setDescription] = useState(product?.description || "");
  const [stock, setStock] = useState(product?.stock ?? 0);
  const [isActive, setIsActive] = useState(product?.isActive ?? true);
  const [category, setCategory] = useState(product?.category || "general");
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  useEffect(() => {
    axios
      .get(`${publicApiOrigin()}/api/categories`, {
        headers: optionalBearerHeaders(),
        withCredentials: true,
      })
      .then((res) => setCategories(res.data.categories || []))
      .catch(() => setCategories([]));
  }, []);

  async function handleSubmit() {
    setIsLoading(true);
    
    try {
      let imageUrls = product?.images || [];

      if (images.length > 0) {
        toast("Image upload is disabled for now");
      }

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

      await axios.put(`${publicApiOrigin()}/api/products/`+productId, productData,
        { headers: optionalBearerHeaders(), withCredentials: true },
      );

      toast.success("Product updated successfully!");
      navigate("/admin/products");
    } catch (err) {
      console.error("Error updating product:", err);
      toast.error("Failed to update product. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="w-full min-h-screen flex justify-center items-center p-4">
      <div className="w-full max-w-2xl bg-white border border-gray-200 rounded-lg shadow-sm p-8">
        <h1 className="text-2xl font-bold mb-6 text-gray-900">Update Product</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-gray-700">Product ID</label>
            <input
              type="text"
              disabled
              value={productId}
              className="w-full border border-gray-300 h-10 rounded-md px-3 bg-gray-100 text-gray-600"
            />
          </div>

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
              onChange={(e) => setImages(e.target.files)}
              disabled
              className="w-full border border-gray-300 rounded-md px-3 py-2 file:mr-4 file:py-1 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-accent hover:file:bg-blue-100"
            />
            {((product?.images) || []).length > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                Current: {((product?.images) || []).length} image(s) uploaded
              </p>
            )}
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
            {isLoading ? "Updating..." : "Update Product"}
          </button>
        </div>
      </div>
    </div>
  );
}