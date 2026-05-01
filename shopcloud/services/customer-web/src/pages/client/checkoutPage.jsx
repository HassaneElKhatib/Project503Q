import { useEffect, useState } from "react"
import { clearCart } from "../../utils/cart"
import { FaPlus } from "react-icons/fa6";
import { HiMiniMinus } from "react-icons/hi2";
import { FaRegTrashCan } from "react-icons/fa6";
import { useLocation, useNavigate } from "react-router-dom";
import { MdPerson, MdLocationOn, MdPhone } from "react-icons/md";
import toast from "react-hot-toast";
import axios from "axios";

const FALLBACK_IMAGE =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400'><rect width='100%25' height='100%25' fill='%23f3f4f6'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-family='Arial' font-size='24'>No image</text></svg>";

function resolveImageSrc(image) {
  if (!image || image.startsWith("http://") || image.startsWith("https://")) {
    return FALLBACK_IMAGE;
  }
  return image;
}

export default function CheckoutPage(){
  const location = useLocation();
  const navigate = useNavigate();
  const [cart, setCart] = useState(location.state?.items || []);
  const [user, setUser] = useState({});
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("card");
  const [isPaying, setIsPaying] = useState(false);

  useEffect(
    () => {
      const token = localStorage.getItem("token");
      if(!token){
        toast.error("Please login before checkout");
        navigate("/login");

      }else{
        axios.get(import.meta.env.VITE_BACKEND_URL+"/api/users/me/",
        {
          headers: {
              Authorization: `Bearer ${token}`,
          }

        }).then(
          (res) => {
            const userPayload = res.data?.user ?? res.data ?? {};
            setUser(userPayload);

            const derivedName =
              userPayload.name ||
              [userPayload.firstName, userPayload.lastName].filter(Boolean).join(" ") ||
              "";
            setName(derivedName);
          }
        ).catch(
          (err) => {
            console.error(err);
            toast.error("Failed to fetch user details");
            navigate("/login");
          }
        )
      }
    }, []);

  if (!location.state?.items) {
    toast.error("Please select items to checkout");
    navigate("/products");
    return null; 
  }

  function getTotal() {
    let total = 0;
    cart.forEach(
      (item) => {
        total += item.price * item.quantity;
      }
    )
    return total;
  }

  async function placeOrder() {
    const token = localStorage.getItem("token");
    if (token == null) {
      toast.error("Please login to place an order");
      navigate("/login");
      return;
    }

    if (!address.trim() || !phone.trim()) {
      toast.error("Please fill in all required fields");
      return;
    }
    if (isPaying) {
      return;
    }

    const order = {
      address: {
        name: name || user.name || "",
        line1: address,
        line2: "",
        city: "",
        postalCode: "",
        country: "",
        phone: phone,
      },
      items: cart.map((item) => ({
        productId: item.productId,
        name: item.name || "",
        price: Number(item.price || 0),
        image: item.image || "",
        quantity: item.quantity
      }))
    };

    try{
        setIsPaying(true);
        await new Promise((resolve) => setTimeout(resolve, 1200));
        const response = await axios.post(import.meta.env.VITE_BACKEND_URL + "/api/orders", order, {
            headers: {
                Authorization: `Bearer ${token}`,
            }
        });

        await clearCart();
        
        toast.success("Payment approved and order placed successfully");
        navigate("/order-confirmation", {
          state: {
            order: response.data,
            invoice: response.data?.invoice || null,
            paymentMethod,
          },
        });

    }catch(err){
        console.error(err);
        toast.error("Failed to place order");
        return;
    } finally {
      setIsPaying(false);
    }
  }

  return(
    <div className="w-full min-h-screen pb-[10px] flex flex-col bg-primary items-center gap-[20px] md:gap-[30px] my-[20px] text-secondary px-[15px] md:px-0">
      
      {/* Page Title */}
      <div className="w-full max-w-[800px] text-center mb-[5px]">
        <h1 className="text-2xl md:text-3xl font-bold text-secondary">Checkout</h1>
        <p className="text-gray-600 mt-2">Review your order and complete your purchase</p>
      </div>

      {/* Cart Items */}
      {
        cart.map(
          (item, index) => {
            return(
              <div key={item.productId} className="w-full max-w-[800px] min-h-[120px] md:h-[100px] flex flex-col md:flex-row shadow-2xl rounded-2xl bg-white">
                
                {/* Mobile Layout */}
                <div className="md:hidden flex flex-col">
                  {/* Top Row */}
                  <div className="flex flex-row">
                    {/* Image */}
                    <div className="w-[100px] h-[100px] flex-shrink-0">
                      <img
                        src={resolveImageSrc(item.image)}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.onerror = null;
                          e.currentTarget.src = FALLBACK_IMAGE;
                        }}
                      />
                    </div>
                    
                    {/* Name, Price and Remove Button */}
                    <div className="flex-1 flex flex-col justify-center p-[15px] relative">
                      <span className="font-bold text-[23px]">{item.name}</span>
                      <span className="font-semibold text-[18px] text-gray-600">
                        ${item.price.toLocaleString("en-US", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                      
                      {/* Remove Button */}
                      <button 
                        className="absolute top-[10px] right-[10px] w-[25px] h-[25px] rounded-full bg-red-500 flex justify-center items-center border-red-500 border-[2px] text-white hover:bg-white cursor-pointer hover:text-red-500" 
                        onClick={() => {
                          const newCart = [...cart];
                          newCart.splice(index, 1);
                          setCart(newCart);
                        }}
                      >
                        <FaRegTrashCan className="text-xs" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Bottom Row */}
                  <div className="flex flex-row justify-between items-center p-[15px] pt-0 border-t border-gray-100">
                    {/* Quantity Controls */}
                    <div className="flex flex-row items-center gap-[10px] mt-[15px]">
                      <button 
                        className="bg-accent w-[30px] h-[30px] flex items-center justify-center rounded-full cursor-pointer hover:bg-accent-hover text-white" 
                        onClick={() => {
                          const newCart = [...cart];
                          newCart[index].quantity -= 1;
                          if (newCart[index].quantity <= 0) {
                            newCart.splice(index, 1);
                          }
                          setCart(newCart);
                        }}
                      >
                        <HiMiniMinus className="font-semibold"/>
                      </button>
                      
                      <span className="font-semibold text-lg min-w-[30px] text-center">
                        {item.quantity}
                      </span>
                      
                      <button 
                        className="bg-accent w-[30px] h-[30px] flex items-center justify-center rounded-full cursor-pointer hover:bg-accent-hover text-white" 
                        onClick={() => {
                          const newCart = [...cart];
                          newCart[index].quantity += 1;
                          setCart(newCart);
                        }}
                      >
                        <FaPlus className="font-semibold"/>
                      </button>
                    </div>
                    
                    {/* Item Total */}
                    <div className="flex flex-col items-end">
                      <span className="text-[15px] text-gray-500">Total</span>
                      <span className="font-bold text-[20px]">
                        ${(item.quantity * item.price).toLocaleString("en-US", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Desktop Layout */}
                <div className="hidden md:flex md:flex-row w-full">
                  {/* Image */}
                  <div className="w-[100px] rounded-l-2xl overflow-hidden flex-shrink-0">
                    <img
                      src={resolveImageSrc(item.image)}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.currentTarget.onerror = null;
                        e.currentTarget.src = FALLBACK_IMAGE;
                      }}
                    />
                  </div>

                  {/* Name and Price */}
                  <div className="w-[300px] flex flex-col p-[15px] justify-center">
                    <span className="font-bold">{item.name}</span>
                    <span className="font-semibold">${item.price.toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}</span>
                  </div>

                  {/* Quantity */}
                  <div className="w-[200px] flex flex-row items-center justify-center gap-[15px]">
                    <button 
                      className="bg-accent w-[30px] h-[30px] flex items-center justify-center rounded-full cursor-pointer hover:bg-accent-hover text-white" 
                      onClick={() => {
                        const newCart = [...cart];
                        newCart[index].quantity += 1;
                        setCart(newCart);
                      }}
                    >
                      <FaPlus className="font-semibold"/>
                    </button>
                    <span className="font-semibold flex justify-center items-center ">
                      {item.quantity}
                    </span>
                    <button 
                      className="bg-accent w-[30px] h-[30px] flex items-center justify-center rounded-full cursor-pointer hover:bg-accent-hover text-white" 
                      onClick={() => {
                        const newCart = [...cart];
                        newCart[index].quantity -= 1;
                        if (newCart[index].quantity <= 0) {
                          newCart.splice(index, 1);
                        }
                        setCart(newCart);
                      }}
                    >
                      <HiMiniMinus className="font-semibold"/>
                    </button>
                  </div>

                  {/* Total */}
                  <div className="w-[200px] flex justify-end items-center pr-[20px]">
                    <span className="font-semibold text-xl">
                      ${(item.quantity * item.price).toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                  </div>

                  {/* Remove Button */}
                  <div className="relative flex justify-center items-center">
                    <button 
                      className="w-[30px] h-[30px] rounded-full bg-red-500 flex justify-center items-center absolute right-[-40px] border-red-500 border-[2px] text-white hover:bg-white cursor-pointer hover:text-red-500" 
                      onClick={() => {
                        const newCart = [...cart];
                        newCart.splice(index, 1);
                        setCart(newCart);
                      }}
                    >
                      <FaRegTrashCan />
                    </button>
                  </div>
                </div>
              </div>
            )
          }
        )
      }

      {/* Customer Information Form */}
      <div className="w-full max-w-[800px] my-[10px] md:my-[5px]">
        <h2 className="text-xl ml-[10px] md:text-2xl font-bold mt-[8px] md:text-left">Delivery Information</h2>
      </div>

      <div className="w-full max-w-[800px] bg-white shadow-2xl rounded-2xl p-[20px] md:p-[30px]">
        {/* Mobile Layout - Stacked Form */}
        <div className="flex flex-col md:hidden gap-[15px]">
          <div className="relative">
            <MdPerson className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl" />
            <input 
              className="w-full h-[50px] border border-gray-300 rounded-lg pl-[45px] pr-[15px] text-base focus:border-blue-500 focus:outline-none" 
              type="text"
              placeholder="Enter Your Name"
              value={name}
              onChange={(e) => setName(e.target.value)} 
            />
          </div>
          
          <div className="relative">
            <MdLocationOn className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl" />
            <input 
              className="w-full h-[50px] border border-gray-300 rounded-lg pl-[45px] pr-[15px] text-base focus:border-blue-500 focus:outline-none" 
              type="text"
              placeholder="Enter Your Address"
              value={address}
              onChange={(e) => setAddress(e.target.value)} 
            />
          </div>
          
          <div className="relative">
            <MdPhone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl" />
            <input 
              className="w-full h-[50px] border border-gray-300 rounded-lg pl-[45px] pr-[15px] text-base focus:border-blue-500 focus:outline-none" 
              type="text"
              placeholder="Enter Your Phone Number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)} 
            />
          </div>
        </div>

        {/* Desktop Layout - Horizontal Form */}
        <div className="hidden md:flex md:flex-row justify-center items-center gap-[15px]">
          <div className="relative">
            <MdPerson className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl" />
            <input 
              className="w-[220px] h-[50px] border border-gray-300 rounded-lg pl-[45px] pr-[15px] focus:border-blue-500 focus:outline-none" 
              type="text"
              placeholder="Enter Your Name"
              value={name}
              onChange={(e) => setName(e.target.value)} 
            />
          </div>
          
          <div className="relative">
            <MdLocationOn className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl" />
            <input 
              className="w-[220px] h-[50px] border border-gray-300 rounded-lg pl-[45px] pr-[15px] focus:border-blue-500 focus:outline-none" 
              type="text"
              placeholder="Enter Your Address"
              value={address}
              onChange={(e) => setAddress(e.target.value)} 
            />
          </div>
          
          <div className="relative">
            <MdPhone className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl" />
            <input 
              className="w-[220px] h-[50px] border border-gray-300 rounded-lg pl-[45px] pr-[15px] focus:border-blue-500 focus:outline-none" 
              type="text"
              placeholder="Enter Your Phone Number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)} 
            />
          </div>
        </div>
      </div>

      <div className="w-full max-w-[800px] bg-white shadow-2xl rounded-2xl p-[20px] md:p-[30px]">
        <h2 className="text-xl md:text-2xl font-bold mb-3">Payment</h2>
        <p className="text-sm text-gray-600 mb-4">Simulated payment for local testing.</p>
        <div className="flex gap-4 flex-wrap">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="paymentMethod"
              value="card"
              checked={paymentMethod === "card"}
              onChange={(e) => setPaymentMethod(e.target.value)}
            />
            Card (simulated)
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="paymentMethod"
              value="cash_on_delivery"
              checked={paymentMethod === "cash_on_delivery"}
              onChange={(e) => setPaymentMethod(e.target.value)}
            />
            Cash on delivery
          </label>
        </div>
      </div>
      
      {/* Total and Place Order Section */}
      <div className="w-full max-w-[800px] min-h-[80px] md:h-[100px] flex flex-col md:flex-row justify-between md:justify-end items-center shadow-2xl rounded-2xl bg-white p-[20px] relative gap-[15px] md:gap-0">
        
        {/* Place Order Button */}
        <button 
          disabled={isPaying}
          className="w-full md:w-[180px] h-[50px] bg-accent rounded-2xl font-semibold text-white border-accent border-[2px] hover:bg-white hover:text-accent transition-colors cursor-pointer md:absolute md:left-[20px] order-2 md:order-1 disabled:opacity-60 disabled:cursor-not-allowed" 
          onClick={() => {
            placeOrder();
          }}
        >
          {isPaying ? "Processing..." : "Pay & Place Order"}
        </button>
        
        {/* Total Amount */}
        <div className="flex flex-col md:flex-row items-center gap-[5px] md:gap-[10px] order-1 md:order-2">
          <span className="text-sm md:hidden text-gray-600">Grand Total:</span>
          <span className="font-bold text-xl md:text-2xl">
            <span className="hidden md:inline">Total: </span>
            ${getTotal().toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        </div>
      </div>
    </div>
  )
}