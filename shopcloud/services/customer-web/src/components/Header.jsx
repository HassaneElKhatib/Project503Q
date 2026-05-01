import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { TiShoppingCart } from "react-icons/ti";
import { GiHamburgerMenu } from "react-icons/gi";
import { HiHome } from "react-icons/hi";
import { BiStore } from "react-icons/bi";
import { FaInfoCircle } from "react-icons/fa";
import { IoClose } from "react-icons/io5";
import { MdContactSupport, MdRateReview } from "react-icons/md";
import { getCart } from "../utils/cart";
import { getUserById } from "../services/userService";
import { MdSendTimeExtension } from "react-icons/md";
import AuthSection from "./AuthSection";
import brandLogo from "../assets/glow-lab-logo.svg";
import { useHostedCognitoAuth } from "../utils/authMode";
import { publicApiOrigin } from "../utils/publicApiOrigin";

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [cartCount, setCartCount] = useState(0);
  const [user, setUser] = useState(null);
  const cognitoHosted = useHostedCognitoAuth();
  const defaultImage = "https://xaezbcwztkcrkmtakkfg.supabase.co/storage/v1/object/public/skyrek-img/icon-5404125_1920.png";
  const brandName = "ShopCloud";
  const brandSubtitle = "Everyday essentials for everyone";

  useEffect(() => {
    const fetchUser = async () => {
      try {
        if (cognitoHosted) {
          await fetch(`${publicApiOrigin()}/auth/refresh`, {
            method: "POST",
            credentials: "include",
          }).catch(() => null);
        }
        const response = await getUserById();
        setUser(response);
      } catch (error) {
        console.error("Error fetching user data:", error);
      }
    };

    fetchUser();
  }, [cognitoHosted, location.pathname]);

  useEffect(() => {
    loadCartCount();
  }, [location.pathname])

  async function loadCartCount() {
    try {
      const cart = await getCart();
      const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
      setCartCount(totalItems);
    } catch (error) {
      console.error("Error loading cart count:", error);
    }
  }

  return (
    <header className="w-full h-[104px] bg-accent flex justify-center items-center text-white text-2xl mb-[20px] relative px-4 md:px-6">
      {/* Mobile Menu Overlay */}
      {isOpen && (
        <div className="fixed z-[100] top-0 left-0 w-[100vh] h-[100vh] bg-[#00000050]">
          <div className="h-full w-[300px] bg-white flex flex-col">
            {/* Mobile Menu Header */}
            <div className="w-full bg-accent h-[104px] flex items-center">
              <div className="ml-4 flex-1 flex items-center gap-3">
                <img src={brandLogo} alt="ShopCloud logo" className="w-11 h-11 rounded-xl shadow-md object-cover" />
                <div>
                  <p className="text-white font-serif text-2xl font-bold leading-tight">{brandName}</p>
                  <p className="text-white/80 text-xs">{brandSubtitle}</p>
                </div>
              </div>
              <IoClose 
                className="text-white text-4xl hover:text-gray-300 cursor-pointer transition-colors" 
                onClick={() => setIsOpen(false)}
              />
              {/* <h2 className="text-white text-xl font-semibold">Menu</h2> */}
            </div>

            {/* Mobile Menu Items */}
            <div className="w-full h-full flex flex-col p-[45px] items-start gap-[30px]">
              <button
                className="text-accent text-2xl flex flex-row items-center hover:text-accent-hover transition-colors"
                onClick={() => {
                  setIsOpen(false);
                  navigate("/");
                }}
              >
                <HiHome className="text-accent text-2xl mr-3 hover:text-accent-hover transition-colors" />
                Home
              </button>

              <button
                className="text-accent text-2xl flex flex-row items-center hover:text-accent-hover transition-colors"
                onClick={() => {
                  setIsOpen(false);
                  navigate("/products");
                }}
              >
                <BiStore className="text-accent text-2xl mr-3 hover:text-accent-hover transition-colors" />
                Products
              </button>

              <button
                className="text-accent text-2xl flex flex-row items-center hover:text-accent-hover transition-colors"
                onClick={() => {
                  setIsOpen(false);
                  navigate("/reviews");
                }}
              >
                <MdRateReview className="text-accent text-2xl mr-3 hover:text-accent-hover transition-colors" />
                Reviews
              </button>

              <button
                className="text-accent text-2xl flex flex-row items-center hover:text-accent-hover transition-colors"
                onClick={() => {
                  setIsOpen(false);
                  navigate("/aboutUS");
                }}
              >
                <FaInfoCircle className="text-accent text-2xl mr-3 hover:text-accent-hover transition-colors" />
                About Us
              </button>

              <button
                className="text-accent text-2xl flex flex-row items-center hover:text-accent-hover transition-colors"
                onClick={() => {
                  setIsOpen(false);
                  navigate("/contactUS");
                }}
              >
                <MdContactSupport className="text-accent text-2xl mr-3 hover:text-accent-hover transition-colors" />
                Contact Us
              </button>

              {user ? (
                  <button
                    className="text-accent text-2xl flex flex-row items-center hover:text-accent-hover transition-colors"
                    onClick={() => {
                      setIsOpen(false);
                      navigate("/orders");
                    }}
                  >
                    <MdSendTimeExtension className="text-accent text-2xl mr-3 hover:text-accent-hover transition-colors" />
                    Orders
                  </button>
                ) : ("")
              }

              <button
                className="text-accent text-2xl flex flex-row items-center hover:text-accent-hover transition-colors"
                onClick={() => {
                  setIsOpen(false);
                  navigate("/cart");
                }}
              >
                <TiShoppingCart className="text-accent text-2xl mr-3 hover:text-accent-hover transition-colors" />
                Cart

                {cartCount > 0 && (
                  <span className="absolute hidden  top-[-8px] left-[18px] bg-red-500 text-white text-xs rounded-full w-[20px] h-[20px] lg:flex items-center justify-center">
                    {cartCount}
                  </span>
                  )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hamburger Menu Button*/}
      <GiHamburgerMenu 
        className="text-white text-4xl absolute left-[20px] md:hidden cursor-pointer hover:text-secondary transition-colors" 
        onClick={() => setIsOpen(true)}
      />

      {/* Desktop Navigation */}
      <Link to="/" className="hidden md:flex absolute left-0 top-0 h-[104px] ml-3 lg:ml-5 items-center">
        <div className="flex items-center gap-3">
          <img src={brandLogo} alt="ShopCloud logo" className="w-12 h-12 rounded-xl shadow-md object-cover border border-white/40" />
          <div>
            <p className="text-white font-serif text-2xl lg:text-3xl font-bold leading-tight tracking-wide">{brandName}</p>
            <p className="text-white/80 text-xs lg:text-sm">{brandSubtitle}</p>
          </div>
        </div>
      </Link>
      <div className="hidden md:flex justify-center items-center mt-1">
        <Link to="/" className="text-white text-lg lg:text-xl hover:text-secondary transition-colors flex flex-row items-center">
          <HiHome className="mr-2" />
          Home
        </Link>
        <Link to="/products" className="ml-5 text-white text-lg lg:text-xl hover:text-secondary transition-colors flex flex-row items-center">
          <BiStore className="mr-2" />
          Products
        </Link>
        <Link to="/reviews" className="ml-5 text-white text-lg lg:text-xl hover:text-secondary transition-colors flex flex-row items-center justify-center">
          <MdRateReview className="mr-2" />
          Site Reviews
        </Link>
        <Link to="/aboutUS" className="ml-5 text-white text-lg lg:text-xl hover:text-secondary transition-colors flex flex-row items-center">
          <FaInfoCircle className="mr-2" />
          About Us
        </Link>
        <Link to="/contactUS" className="ml-5 text-white text-lg lg:text-xl hover:text-secondary transition-colors flex flex-row items-center">
          <MdContactSupport className="mr-1" />
          Contact Us
        </Link>
      </div>
      <div className="absolute flex right-[16px] md:right-[20px] gap-6 md:gap-8 items-center">
        <AuthSection user={user} defaultImage={defaultImage} />

        <Link 
          to="/cart" 
          className="hidden md:right-[50px] md:flex hover:text-secondary transition-colors  flex-row items-center"
        >
          <TiShoppingCart className="text-3xl" />
          {cartCount > 0 && (
            <span className="absolute top-[-8px] right-[-8px] bg-red-500 text-white text-xs rounded-full w-[22px] h-[22px] flex items-center justify-center font-bold">
              {cartCount}
            </span>
          )}
        </Link>
      </div>
        
    </header>
  );
}