import axios from "axios";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";

export default function ForgetPasswordPage() {
  const[emailSent, setEmailSent] = useState(false);
  const[email, setEmail] = useState("");
  const[OTP, setOTP] = useState("");
  const navigate = useNavigate();


  async function sendOTP(){
    try{
      await axios.post(import.meta.env.VITE_BACKEND_URL+"/api/users/send-otp", { email: email });
      toast.success("OTP sent to your email");
      setEmailSent(true);

    }catch(error){
      console.log(error);
      toast.error("Failed to send OTP");
    }
  }

  async function verifyOTP(){
    try{
      const response = await axios.post(import.meta.env.VITE_BACKEND_URL+"/api/users/verify-otp", { email: email, otp: OTP });
      toast.success(response.data.message);

      const resetToken = response.data.token;
      
      navigate("/reset-password", { state: { resetToken: resetToken } });
    }catch(error){
      console.log(error);
      toast.error(error.response?.data?.message || "Failed to verify OTP");
    }
  }

  return (
    <div className="w-full min-h-screen flex justify-center items-center bg-primary">
      {
        !emailSent ? (
          <div className="w-[500px] h-[400px] bg-white shadow-2xl rounded-[30px] flex flex-col justify-center items-center relative gap-[12px] p-6">
        
          {/* Heading */}
          <h1 className="absolute top-[65px] text-2xl font-semibold text-secondary flex flex-col justify-center items-center">
            Reset Password
          </h1>
          
          {/* Subtext */}
          <div className="flex flex-col items-center text-center mt-16 gap-1">
            <h2 className="text-xl text-secondary font-medium">
              Enter Your Email Address
            </h2>
            <span className="text-secondary text-sm">
              You will receive an OTP code
            </span>
          </div>
          
          {/* Input */}
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            className="w-[300px] h-[40px] border-2 border-accent rounded-xl px-3 focus:outline-none focus:border-accent-hover focus:ring-2 focus:ring-accent-hover transition"
            onChange={(e) => setEmail(e.target.value)}
          />
          
          {/* Button */}
          <button className="w-[300px] h-[40px] bg-accent text-white rounded-xl mt-2 hover:bg-accent-hover transition" onClick={sendOTP}>
            Send OTP
          </button>
          
          {/* Back link */}
          <Link
            to="/login"
            className="text-accent hover:underline text-sm mt-2"
          >
            Back to Login page
          </Link>
        </div>
        ) : (
          <div className="w-[500px] h-[400px] bg-white shadow-2xl rounded-[30px] flex flex-col justify-center items-center relative gap-[12px] p-6">
        
            {/* Heading */}
            <h1 className="absolute top-[65px] text-2xl font-semibold text-secondary flex flex-col justify-center items-center">
              OTP Verification
            </h1>
            
            {/* Subtext */}
            <div className="flex flex-col items-center text-center mt-16 gap-1">
              <h2 className="text-xl text-secondary font-medium">
                Enter Your OTP
              </h2>
              <span className="text-secondary text-sm">
                We have sent an OTP to your email
              </span>
            </div>
            
            {/* Input */}
            <input
              type="text"
              placeholder="Enter OTP"
              value={OTP}
              className="w-[300px] h-[40px] border-2 border-accent rounded-xl px-3 focus:outline-none focus:border-accent-hover focus:ring-2 focus:ring-accent-hover transition"
              onChange={(e) => setOTP(e.target.value)}
            />
            
            {/* Button */}
            <button className="w-[300px] h-[40px] bg-accent text-white rounded-xl mt-2 hover:bg-accent-hover transition" onClick={verifyOTP}>
              Verify OTP
            </button>
            
            {/* Back link */}
            <Link
              to="/login"
              className="text-accent hover:underline text-sm mt-2"
            >
              Back to Login page
            </Link>
          </div>  
        )
      }
      
    </div>
  );
}
