import axios from "axios";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import { useHostedCognitoAuth } from "../utils/authMode";
import { publicApiOrigin } from "../utils/publicApiOrigin";

export default function ForgetPasswordPage() {
  const cognitoHosted = useHostedCognitoAuth();

  useEffect(() => {
    if (!cognitoHosted) return;
    window.location.replace(`/auth/login?next=${encodeURIComponent("/")}`);
  }, [cognitoHosted]);

  const [emailSent, setEmailSent] = useState(false);
  const [email, setEmail] = useState("");
  const [OTP, setOTP] = useState("");
  const [codeHint, setCodeHint] = useState("");
  const navigate = useNavigate();

  if (cognitoHosted) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center text-slate-600">
        Opening password recovery…
      </div>
    );
  }

  async function sendOTP() {
    try {
      const trimmed = email.trim();
      if (!trimmed) {
        toast.error("Enter your email");
        return;
      }
      const res = await axios.post(`${publicApiOrigin()}/api/auth/forgot-password`, { email: trimmed });
      const emailed = Boolean(res.data.emailSent);
      if (emailed) {
        toast.success("If this email is registered, a reset code was sent.");
      } else {
        toast(
          "Email could not be sent (SMTP not configured). Use the code shown below if one appears.",
          { icon: "⚠️" },
        );
      }
      setCodeHint(!emailed && res.data.debug_code ? String(res.data.debug_code) : "");
      setEmailSent(true);
    } catch (error) {
      console.log(error);
      toast.error(error.response?.data?.detail || "Failed to send reset code");
    }
  }

  function continueToReset() {
    const trimmed = OTP.trim();
    if (!trimmed) {
      toast.error("Enter the code from your email");
      return;
    }
    navigate("/reset-password", { state: { email: email.trim(), resetCode: trimmed } });
  }

  return (
    <div className="w-full min-h-screen flex justify-center items-center bg-primary">
      {!emailSent ? (
        <div className="w-[500px] h-[400px] bg-white shadow-2xl rounded-[30px] flex flex-col justify-center items-center relative gap-[12px] p-6">
          <h1 className="absolute top-[65px] text-2xl font-semibold text-secondary flex flex-col justify-center items-center">
            Reset Password
          </h1>

          <div className="flex flex-col items-center text-center mt-16 gap-1">
            <h2 className="text-xl text-secondary font-medium">Enter Your Email Address</h2>
            <span className="text-secondary text-sm">You will receive a reset code</span>
          </div>

          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            className="w-[300px] h-[40px] border-2 border-accent rounded-xl px-3 focus:outline-none focus:border-accent-hover focus:ring-2 focus:ring-accent-hover transition"
            onChange={(e) => setEmail(e.target.value)}
          />

          <button
            className="w-[300px] h-[40px] bg-accent text-white rounded-xl mt-2 hover:bg-accent-hover transition"
            onClick={sendOTP}
          >
            Send code
          </button>

          <Link to="/login" className="text-accent hover:underline text-sm mt-2">
            Back to Login page
          </Link>
        </div>
      ) : (
        <div className="w-[500px] h-[400px] bg-white shadow-2xl rounded-[30px] flex flex-col justify-center items-center relative gap-[12px] p-6">
          <h1 className="absolute top-[65px] text-2xl font-semibold text-secondary flex flex-col justify-center items-center">
            Enter reset code
          </h1>

          <div className="flex flex-col items-center text-center mt-16 gap-1">
            <h2 className="text-xl text-secondary font-medium">Check your email</h2>
            <span className="text-secondary text-sm">Enter the one-time code we sent</span>
          </div>

          {codeHint ? (
            <p className="text-xs text-amber-700 px-4 text-center">
              Email unavailable — use this code: <strong>{codeHint}</strong>
            </p>
          ) : null}

          <input
            type="text"
            placeholder="Enter code"
            value={OTP}
            className="w-[300px] h-[40px] border-2 border-accent rounded-xl px-3 focus:outline-none focus:border-accent-hover focus:ring-2 focus:ring-accent-hover transition"
            onChange={(e) => setOTP(e.target.value)}
          />

          <button
            className="w-[300px] h-[40px] bg-accent text-white rounded-xl mt-2 hover:bg-accent-hover transition"
            onClick={continueToReset}
          >
            Continue
          </button>

          <Link to="/login" className="text-accent hover:underline text-sm mt-2">
            Back to Login page
          </Link>
        </div>
      )}
    </div>
  );
}
