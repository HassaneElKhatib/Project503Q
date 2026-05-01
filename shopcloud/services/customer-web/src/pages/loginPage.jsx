import { Link, useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react"
import toast from "react-hot-toast";
import { useGoogleLogin } from '@react-oauth/google';
import { handleGoodleLogin, handleLogin, handleVerifyOtp } from "../services/authService";
import { useHostedCognitoAuth } from "../utils/authMode";

export default function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const cognitoHosted = useHostedCognitoAuth();

  const[email, setEmail] = useState("");
  const[password, setPassword] = useState("");
  const[isLoading, setIsLoading] = useState(false);
  const[isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [mfaToken, setMfaToken] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [otpHint, setOtpHint] = useState("");
  const isGoogleLoginEnabled = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID);
  const serumVisual =
    "/ecommerce-auth-bg.jpg";

  useEffect(() => {
    if (!cognitoHosted) return;
    const isAdminLogin = location.pathname.includes("/admin/login");
    const authPath = isAdminLogin ? "/auth/admin/login" : "/auth/login";
    const next = isAdminLogin ? "/admin" : "/client/dashboard";
    window.location.replace(`${authPath}?next=${encodeURIComponent(next)}`);
  }, [cognitoHosted, location.pathname]);

  const googleLogin = useGoogleLogin({
    onSuccess: async (response) => { 
      try {
        setIsGoogleLoading(true);

        const role = await handleGoodleLogin(response.access_token);

        if (role === "admin") {
          navigate("/admin");

        } else if (role === "user") {
          navigate("/");
        }

      } catch (err) {
        console.error(err);

      } finally {
        setIsGoogleLoading(false);
      }
    },
    onError: () => {
      toast.error("Google login failed!");
    }
  });

  const login = async () => {
    try {
      setIsLoading(true);
      const loginResult = await handleLogin(email, password);

      if (loginResult?.mfaRequired) {
        setMfaToken(loginResult.mfaToken);
        const showDevCode = Boolean(loginResult.debugOtp) && loginResult.emailSent !== true;
        setOtpHint(showDevCode ? `Verification code (email unavailable): ${loginResult.debugOtp}` : "");
        setIsLoading(false);
        return;
      }

      setIsLoading(false);

    }catch(err) {
      console.log(err);
      setIsLoading(false);
    }
  } 

  const verifyOtp = async () => {
    if (!mfaToken || !otpCode.trim()) {
      toast.error("Enter OTP code first");
      return;
    }
    setIsLoading(true);
    const role = await handleVerifyOtp(mfaToken, otpCode.trim());
    setIsLoading(false);
    if (role === "admin") {
      navigate("/admin");
    } else if (role === "user") {
      navigate("/");
    }
  };

  if (cognitoHosted) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center text-slate-600">
        Redirecting to secure sign-in…
      </div>
    );
  }

  return (
    <div
      className="w-full min-h-screen bg-cover bg-center flex items-center justify-center px-4 py-8"
      style={{ backgroundImage: `url(${serumVisual})` }}
    >
      <div className="w-full max-w-xl flex justify-center items-center backdrop-blur-sm shadow-2xl rounded-[30px] p-6 sm:p-10">
        <div className="w-full max-w-md flex flex-col gap-5">
            <h1 className="font-serif text-3xl font-bold text-accent-hover text-center">
              Sign in to ShopCloud
            </h1>
            <p className="text-sm text-slate-600 text-center">
              Access your account to shop electronics, fashion, home essentials, and more.
            </p>

            <div className="w-full flex flex-col">
              <span className="text-sm text-accent-hover mb-1 font-semibold">Email</span>
              <input
                type="text"
                className="w-full h-11 text-accent-hover px-3 border rounded-xl border-accent"
                placeholder="eg: example@email.com"
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="w-full flex flex-col">
              <span className="text-sm text-accent-hover mb-1 font-semibold">Password</span>
              <input
                type="password"
                className="w-full h-11 text-accent-hover border px-3 border-accent rounded-xl"
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div className="w-full relative mb-1">
              <Link
                to="/forget-password"
                className="text-accent text-sm hover:text-accent-hover"
              >
                Forget Password?
              </Link>
            </div>

            {!mfaToken ? (
              <button
                disabled={isLoading}
                className="w-full h-11 bg-accent-hover rounded-xl text-base text-white hover:bg-accent cursor-pointer transition-all duration-300"
                onClick={login}
              >
                {isLoading ? "Loading..." : "Login Now"}
              </button>
            ) : (
              <>
                <input
                  type="text"
                  className="w-full h-11 text-accent-hover border px-3 border-accent rounded-xl"
                  placeholder="Enter OTP sent to email"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                />
                {otpHint ? <p className="text-xs text-accent-hover">{otpHint}</p> : null}
                <button
                  disabled={isLoading}
                  className="w-full h-11 bg-accent-hover rounded-xl text-base text-white hover:bg-accent cursor-pointer transition-all duration-300"
                  onClick={verifyOtp}
                >
                  {isLoading ? "Verifying..." : "Verify OTP"}
                </button>
              </>
            )}
            <button
              disabled={isGoogleLoading || !isGoogleLoginEnabled}
              className="w-full h-11 bg-accent-hover rounded-xl text-base text-white hover:bg-accent cursor-pointer transition-all duration-300"
              onClick={() => {
                if (!isGoogleLoginEnabled) {
                  toast.error("Google login is disabled in local mode.");
                  return;
                }
                googleLogin();
              }}
            >
              {isGoogleLoading ? "Loading..." : (isGoogleLoginEnabled ? "Google Login" : "Google Login (disabled)")}
            </button>

            <p className="text-slate-700 text-sm text-center">
              Don't have an account?{" "}
              <Link to="/register" className="text-accent hover:text-accent-hover">
                Sign up
              </Link>{" "}
              from here
            </p>
        </div>
      </div>
    </div>
  );
}
