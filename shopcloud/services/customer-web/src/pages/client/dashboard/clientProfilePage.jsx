import { useEffect, useState } from "react";
import { FaUser, FaEnvelope, FaPhone, FaLock, FaCamera } from "react-icons/fa";
import TitleHeaderDashboard from "../../../components/TitleHeader";
import { useUpdatePassword, useUpdateUser, useUser } from "../../../hooks/useUserQueries";
import uploadFile from "../../../utils/mediaUpload";
import Loader from "../../../components/loader";
import toast from "react-hot-toast";

export default function ClientProfilePage() {
  const [isEditing, setIsEditing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const defaultImage = "https://xaezbcwztkcrkmtakkfg.supabase.co/storage/v1/object/public/skyrek-img/icon-5404125_1920.png";
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    image: null,
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [originalData, setOriginalData] = useState({});

  const { data: userData, isLoading, isError, error } = useUser();
  const updateUserMutation = useUpdateUser();
  const updatePasswordMutation = useUpdatePassword();

  useEffect(() => {
    if(userData) {
      const initialData = {
        firstName: userData.firstName || "",
        lastName: userData.lastName || "",
        email: userData.email || "",
        phone: userData.phone || "",
        image: userData.image || null,
      }

      setFormData(prev => ({...prev, ...initialData}) );
      setOriginalData(initialData);
    }
  }, [userData]);

  const handleChange = async (e) => {
    const { name, type, files, value } = e.target;

    if(type === "file") {
      const file = files?.[0];
      
      try {
        setIsUploading(true);
        const imageUrl = await uploadFile(file);
        setFormData(prev => ({...prev, image: imageUrl}) );
      }catch(err) {
        console.error("Image upload failed:", err);
      } finally {
        setIsUploading(false);
      }
      return;
    }

    setFormData(prev => ({ ...prev, [name]: value}));

  };

  const handleSave = async () => {
    const dataToUpdate = {
      firstName: formData.firstName,
      lastName: formData.lastName,
      phone: formData.phone,
      image: formData.image,
    }

    // Update React Query mutation
    updateUserMutation.mutate(dataToUpdate, {
      onSuccess: (updateUser) => {
        setOriginalData(updateUser);
        setIsEditing(false);
      }
    });
  }

  const handleCancel = () => {
    setIsEditing(false);
    setFormData(prev => ({...prev, ...originalData}));
  }

  const validateionPasswordChange = () => {
    if(!formData.currentPassword || !formData.newPassword || !formData.confirmPassword) {
      toast.error("All password fields are required.");
      return false;
    }

    if(formData.newPassword !== formData.confirmPassword) {
      toast.error("New password and confirm password do not match.");
      return false;
    }
    return true;
  }

  const handleChangePassword = () => {
    if(!validateionPasswordChange()) return;

    updatePasswordMutation.mutate({
      currentPassword: formData.currentPassword,
      newPassword: formData.newPassword
    },
    {
      onSuccess: () => {
        setFormData(prev => ({
          ...prev,
          currentPassword: "",
          newPassword: "",
          confirmPassword: ""
        }));
      }
    });
  }

  // Loading state
  if (isLoading) {
    return (
      <Loader />
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="text-lg text-red-600">
          Error loading profile: {error?.message}
        </div>
      </div>
    );
  }

  return (
    <div>
      <TitleHeaderDashboard 
        title="Profile" 
        subtitle="Manage your profile information"
      />

      {/* Profile Information Card */}
      <div className="bg-white m-10 p-8 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-gray-800">Profile Information</h2>
          {!isEditing ? (
            <button
              onClick={() => {
                setIsEditing(true);
                handleChange;
              }}
              className="bg-accent text-white px-5 py-2 rounded-lg hover:bg-accent-hover transition-colors"
            >
              Edit Profile
            </button>
          ) : (
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setIsEditing(false);
                  handleCancel;
                }}
                dissabled={isUploading}
                className="bg-gray-300 text-gray-700 px-5 py-2 rounded-lg hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
              <button
                disabled={isUploading}
                onClick={handleSave}
                className={`px-5 py-2 rounded-lg transition-colors ${
                  isUploading 
                    ? "bg-gray-400 text-white cursor-not-allowed" 
                    : "bg-green-600 text-white hover:bg-green-700"
                }`}
              >
                {isUploading ? "Uploading..." : "Save Changes"}
              </button>
            </div>
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          
          {/* Profile Picture Section */}
          <div className="flex flex-col items-center justify-start gap-4 lg:border-r lg:pr-8">
            <div className="relative">
              <img 
                src={formData.image || defaultImage} 
                alt="Profile" 
                className={`w-40 h-40 rounded-full object-cover border-4 border-gray-200 ${
                  isUploading ? "opacity-50" : ""
                }`}
              />
              {isUploading && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-sm font-semibold text-gray-700">
                    Uploading...
                  </div>
                </div>
              )}
            </div>
            
            {isEditing && (
              <div className="w-full">
                <label 
                  htmlFor="profileImage" 
                  className="flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg cursor-pointer transition-colors border border-gray-300"
                >
                  <FaCamera />
                  Upload New Picture
                </label>
                <input 
                  id="profileImage"
                  type="file" 
                  accept="image/*"
                  disabled={isUploading}
                  onChange={handleChange}
                  className="hidden" 
                />
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Max size: 5MB
                </p>
              </div>
            )}
          </div>

          {/* Form Fields Section */}
          <div className="lg:col-span-2 space-y-5">
            {/* First Name */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <FaUser className="text-gray-400" />
                First Name
              </label>
              <input 
                type="text" 
                name="firstName"
                disabled={!isEditing}
                value={formData.firstName}
                onChange={handleChange}
                placeholder="Enter your first name"
                className="border-2 border-gray-300 rounded-lg p-3 w-full focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600 disabled:cursor-not-allowed transition-colors" 
              />
            </div>

            {/* Last Name */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <FaUser className="text-gray-400" />
                Last Name
              </label>
              <input 
                type="text" 
                name="lastName"
                disabled={!isEditing}
                value={formData.lastName}
                onChange={handleChange}
                placeholder="Enter your last name"
                className="border-2 border-gray-300 rounded-lg p-3 w-full focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600 disabled:cursor-not-allowed transition-colors" 
              />
            </div>

            {/* Email */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <FaEnvelope className="text-gray-400" />
                Email Address
              </label>
              <input 
                type="email" 
                name="email"
                value={originalData.email}
                disabled
                placeholder="your.email@example.com"
                className="border-2 border-gray-300 rounded-lg p-3 w-full bg-gray-50 text-gray-600 cursor-not-allowed" 
              />
              <p className="text-xs text-gray-500 mt-1">
                Email cannot be changed
              </p>
            </div>

            {/* Phone Number */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <FaPhone className="text-gray-400" />
                Phone Number
              </label>
              <input 
                type="tel" 
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                disabled={!isEditing}
                placeholder="+94 77 123 4567"
                className="border-2 border-gray-300 rounded-lg p-3 w-full focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent disabled:bg-gray-50 disabled:text-gray-600 disabled:cursor-not-allowed transition-colors" 
              />
            </div>
          </div>
        </div>
      </div>

      {/* Change Password Card */}
      <div className="bg-white m-10 p-8 rounded-lg shadow-sm">
        <h2 className="text-2xl font-semibold text-gray-800 mb-6 flex items-center gap-2">
          <FaLock className="text-gray-400" />
          Change Password
        </h2>

        <div className="grid md:grid-cols-3 gap-5">
          {/* Current Password */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Current Password
            </label>
            <input 
              type="password" 
              name="currentPassword"
              value={formData.currentPassword}
              onChange={handleChange}
              placeholder="Enter current password"
              className="border-2 border-gray-300 rounded-lg p-3 w-full focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-colors" 
            />
          </div>

          {/* New Password */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              New Password
            </label>
            <input 
              type="password" 
              name="newPassword"
              value={formData.newPassword}
              onChange={handleChange}
              placeholder="Enter new password"
              className="border-2 border-gray-300 rounded-lg p-3 w-full focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-colors" 
            />
          </div>

          {/* Confirm Password */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              Confirm New Password
            </label>
            <input 
              type="password" 
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirm new password"
              className="border-2 border-gray-300 rounded-lg p-3 w-full focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition-colors" 
            />
          </div>
        </div>

        <button 
          className="bg-accent text-white px-6 py-3 rounded-lg mt-6 hover:bg-accent-hover transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed cursor-pointer"
          onClick={handleChangePassword}
        >
          Update Password
        </button>
      </div>
    </div>
  );
}