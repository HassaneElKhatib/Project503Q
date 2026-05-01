import { useEffect, useState } from "react";
import axios from "axios";
import toast from "react-hot-toast";
import TitleHeaderDashboard from "../../components/TitleHeader";

export default function CategoriesAdminPage() {
  const [categories, setCategories] = useState([]);
  const [newName, setNewName] = useState("");
  const [editing, setEditing] = useState({ id: "", name: "" });

  async function loadCategories() {
    try {
      const res = await axios.get(import.meta.env.VITE_BACKEND_URL + "/api/categories", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      setCategories(res.data.categories || []);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load categories");
    }
  }

  useEffect(() => {
    loadCategories();
  }, []);

  async function createCategory() {
    if (!newName.trim()) {
      toast.error("Category name is required");
      return;
    }
    try {
      await axios.post(
        import.meta.env.VITE_BACKEND_URL + "/api/categories",
        { name: newName.trim() },
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      );
      toast.success("Category created");
      setNewName("");
      loadCategories();
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to create category");
    }
  }

  async function saveEdit() {
    if (!editing.id || !editing.name.trim()) return;
    try {
      await axios.put(
        import.meta.env.VITE_BACKEND_URL + `/api/categories/${editing.id}`,
        { name: editing.name.trim() },
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      );
      toast.success("Category updated");
      setEditing({ id: "", name: "" });
      loadCategories();
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to update category");
    }
  }

  async function disableCategory(id) {
    try {
      await axios.delete(import.meta.env.VITE_BACKEND_URL + `/api/categories/${id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      toast.success("Category disabled");
      loadCategories();
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to disable category");
    }
  }

  return (
    <div className="w-full h-full">
      <TitleHeaderDashboard title="Category Management" subtitle="Create, update, and disable store categories." />
      <div className="bg-white p-4 rounded-xl shadow mb-4 flex gap-3 items-center">
        <input
          className="border border-gray-300 rounded-md px-3 py-2 w-[320px]"
          placeholder="New category name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
        />
        <button className="bg-accent text-white px-4 py-2 rounded-md" onClick={createCategory}>
          Add Category
        </button>
      </div>
      <div className="bg-white p-4 rounded-xl shadow">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Name</th>
              <th className="text-left py-2">Slug</th>
              <th className="text-left py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((category) => (
              <tr key={category._id} className="border-b">
                <td className="py-2">
                  {editing.id === category._id ? (
                    <input
                      className="border border-gray-300 rounded px-2 py-1"
                      value={editing.name}
                      onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                    />
                  ) : (
                    category.name
                  )}
                </td>
                <td className="py-2">{category.slug}</td>
                <td className="py-2 flex gap-2">
                  {editing.id === category._id ? (
                    <button className="bg-green-600 text-white px-3 py-1 rounded" onClick={saveEdit}>
                      Save
                    </button>
                  ) : (
                    <button
                      className="bg-blue-600 text-white px-3 py-1 rounded"
                      onClick={() => setEditing({ id: category._id, name: category.name })}
                    >
                      Edit
                    </button>
                  )}
                  <button className="bg-red-600 text-white px-3 py-1 rounded" onClick={() => disableCategory(category._id)}>
                    Disable
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
