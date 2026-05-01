import axios from "axios";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { publicApiOrigin } from "../utils/publicApiOrigin";

export default function ResetPasswordPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const email = location.state?.email;
  const resetCode = location.state?.resetCode;

  useEffect(() => {
    if (!email || !resetCode) {
      toast.error("Invalid access to reset password page.");
      navigate("/login");
    }
  }, [email, resetCode, navigate]);

  async function resetPassword() {
    if (!newPassword || !confirmPassword) {
      toast.error("Please fill in both password fields");
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    try {
      const response = await axios.post(`${publicApiOrigin()}/api/auth/reset-password`, {
        email,
        code: resetCode,
        password: newPassword,
      });
      toast.success(response.data.message || "Password updated");
      navigate("/login");
    } catch (error) {
      console.log(error);
      toast.error(error.response?.data?.detail || "Failed to reset password");
    }
  }

  return (
    <div className="w-full min-h-screen flex justify-center items-center bg-primary">
      <div className="w-[500px] h-[450px] bg-white shadow-2xl rounded-[30px] flex flex-col justify-center items-center relative gap-[12px] p-6">
        <h1 className="absolute top-[65px] text-2xl font-semibold text-secondary flex flex-col justify-center items-center">
          Reset Password
        </h1>

        <div className="flex flex-col items-center text-center mt-16 gap-1">
          <h2 className="text-xl text-secondary font-medium">Enter Your New Password</h2>
          <span className="text-secondary text-sm">Make sure your password is strong</span>
        </div>

        <input
          type="password"
          placeholder="New Password"
          value={newPassword}
          className="w-[300px] h-[40px] border-2 border-accent rounded-xl px-3 focus:outline-none focus:border-accent-hover focus:ring-2 focus:ring-accent-hover transition"
          onChange={(e) => {
            setNewPassword(e.target.value);
          }}
        />

        <input
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          className="w-[300px] h-[40px] border-2 border-accent rounded-xl px-3 focus:outline-none focus:border-accent-hover focus:ring-2 focus:ring-accent-hover transition"
          onChange={(e) => {
            setConfirmPassword(e.target.value);
          }}
        />

        <button
          className="w-[300px] h-[40px] bg-accent text-white rounded-xl mt-2 hover:bg-accent-hover transition"
          onClick={resetPassword}
        >
          Reset Password
        </button>

        <Link to="/login" className="text-accent hover:underline text-sm mt-2">
          Back to Login page
        </Link>
      </div>
    </div>
  );
}
