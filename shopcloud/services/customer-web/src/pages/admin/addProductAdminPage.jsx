import axios from "axios";
import { optionalBearerHeaders } from "../../config/axiosConfig";
import { publicApiOrigin } from "../../utils/publicApiOrigin";
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
  const [imageUrlInput, setImageUrlInput] = useState("");
  const [imageUrls, setImageUrls] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
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
        `${publicApiOrigin()}/api/products`,
        productData,
        { headers: optionalBearerHeaders(), withCredentials: true }
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
            <label className="text-sm font-semibold text-gray-700">Product Images</label>
            <div className="flex gap-2 items-center">
              <input
                type="file"
                accept="image/*"
                multiple
                disabled={isUploading}
                onChange={async (e) => {
                  const files = Array.from(e.target.files || []);
                  if (!files.length) return;
                  setIsUploading(true);
                  const uploaded = [];
                  for (const file of files) {
                    try {
                      const form = new FormData();
                      form.append("file", file);
                      const res = await axios.post(
                        `${publicApiOrigin()}/api/images/upload`,
                        form,
                        { headers: { ...optionalBearerHeaders(), "Content-Type": "multipart/form-data" }, withCredentials: true }
                      );
                      uploaded.push(res.data.url);
                    } catch (err) {
                      console.error("Upload failed:", err);
                      toast.error(`Failed to upload ${file.name}`);
                    }
                  }
                  if (uploaded.length) setImageUrls((prev) => [...prev, ...uploaded]);
                  setIsUploading(false);
                  e.target.value = "";
                }}
                className="flex-1 border border-gray-300 h-10 rounded-md px-3 py-1.5 text-sm file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:bg-accent file:text-white file:font-medium file:cursor-pointer"
              />
              {isUploading && <span className="text-sm text-gray-500 animate-pulse">Uploading...</span>}
            </div>
            <div className="flex gap-2 mt-1">
              <input
                type="url"
                value={imageUrlInput}
                onChange={(e) => setImageUrlInput(e.target.value)}
                placeholder="Or paste an image URL and click Add"
                className="flex-1 border border-gray-300 h-10 rounded-md px-3 focus:ring-2 focus:ring-accent focus:border-transparent text-sm"
              />
              <button
                type="button"
                onClick={() => {
                  const url = imageUrlInput.trim();
                  if (url && !imageUrls.includes(url)) {
                    setImageUrls([...imageUrls, url]);
                    setImageUrlInput("");
                  }
                }}
                className="px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-hover transition-colors font-medium"
              >
                Add
              </button>
            </div>
            {imageUrls.length > 0 && (
              <div className="flex flex-wrap gap-3 mt-2">
                {imageUrls.map((url, idx) => (
                  <div key={idx} className="relative group">
                    <img src={url} alt={`Preview ${idx + 1}`} className="w-20 h-20 object-cover rounded-md border border-gray-200" />
                    <button
                      type="button"
                      onClick={() => setImageUrls(imageUrls.filter((_, i) => i !== idx))}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      x
                    </button>
                  </div>
                ))}
              </div>
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
            {isLoading ? "Adding..." : "Add Product"}
          </button>
        </div>
      </div>
    </div>
  );
}
