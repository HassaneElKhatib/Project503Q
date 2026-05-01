import { useEffect, useState } from "react"
import { addToCart, getCart, getTotal } from "../../utils/cart"
import { FaPlus } from "react-icons/fa6";
import { HiMiniMinus } from "react-icons/hi2";
import { FaRegTrashCan } from "react-icons/fa6";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

const FALLBACK_IMAGE =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400'><rect width='100%25' height='100%25' fill='%23f3f4f6'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-family='Arial' font-size='24'>No image</text></svg>";

function resolveImageSrc(image) {
  if (!image || image.includes("shopcloud.example")) {
    return FALLBACK_IMAGE;
  }
  return image;
}

export default function CartPage(){
  const[cart, setCart] = useState([]);
  const navigate= useNavigate();
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true); 

  useEffect(() => {
    loadCart();
  }, []);

  async function loadCart() {
    try {
      setLoading(true);
      const cartData = await getCart();
      setCart(cartData);
      const totalAmount = await getTotal();
      setTotal(totalAmount);
    } catch (error) {
      console.error("Error loading cart:", error);
      toast.error("Failed to load cart");
    } finally {
      setLoading(false);
    }
  }

  async function updateCart(item, quantityChange) {
    try {
      await addToCart(item, quantityChange);
      await loadCart();
    } catch (error) {
      console.error("Error updating cart:", error);
      toast.error("Failed to update cart");
    }
  }

  async function removeItem(item) {
    try {
      await addToCart(item, -item.quantity);
      await loadCart();
      toast.success("Item removed from cart");
    } catch (error) {
      console.error("Error removing item:", error);
      toast.error("Failed to remove item");
    }
  }

  if (loading) {
    return (
      <div className="w-full h-screen flex justify-center items-center bg-primary">
        <div className="text-xl">Loading cart...</div>
      </div>
    );
  }

  if (cart.length === 0) {
    return (
      <div className="w-full h-screen flex flex-col justify-center items-center bg-primary gap-4">
        <div className="text-2xl font-bold">Your cart is empty</div>
        <button 
          className="bg-accent text-white px-6 py-3 rounded-lg hover:bg-accent-hover"
          onClick={() => navigate("/products")}
        >
          Continue Shopping
        </button>
      </div>
    );
  }

  console.log(cart);
  return(
    <div className="w-full h-full flex flex-col bg-primary items-center gap-[20px] md:gap-[30px] my-[20px] text-secondary px-[15px] md:px-0">
      {
        cart.map(
          (item) => {
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
                          removeItem(item)
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
                          updateCart(item, -1)
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
                          updateCart(item, 1)
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
                        updateCart(item, 1)
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
                        updateCart(item, -1)
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
                        removeItem(item)
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
      
      {/* Total and Checkout Section */}
      <div className="w-full max-w-[800px] min-h-[80px] md:h-[100px] flex flex-col md:flex-row justify-between md:justify-end items-center shadow-2xl rounded-2xl bg-white p-[20px] relative gap-[15px] md:gap-0">
        
        {/* Checkout Button */}
        <button 
          className="w-full md:w-[150px] h-[50px] bg-accent rounded-2xl font-semibold text-white border-accent border-[2px] hover:bg-white hover:text-accent transition-colors md:absolute md:left-[20px] order-2 md:order-1" 
          onClick={() => {
            navigate("/checkout", {
              state: {items: cart}
            });
          }}
        >
          Checkout
        </button>
        
        {/* Total Amount */}
        <div className="flex flex-col md:flex-row items-center gap-[5px] md:gap-[10px] order-1 md:order-2">
          <span className="text-sm md:hidden text-gray-600">Grand Total:</span>
          <span className="font-bold text-xl md:text-2xl">
            <span className="hidden md:inline">Total: </span>
            ${total.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        </div>
      </div>
    </div>
  )
}