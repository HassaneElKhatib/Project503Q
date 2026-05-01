import axios from "axios";
import { optionalBearerHeaders } from "../config/axiosConfig";
import { publicApiOrigin } from "./publicApiOrigin";

const base = publicApiOrigin();

function reqCfg(extra = {}) {
  return {
    withCredentials: true,
    headers: { ...optionalBearerHeaders(), ...(extra.headers || {}) },
    ...extra,
  };
}

function guestCartParse() {
  let cartInString = localStorage.getItem("cart");
  if (cartInString == null) {
    cartInString = "[]";
    localStorage.setItem("cart", cartInString);
  }
  return JSON.parse(cartInString);
}

// Get cart from localStorage or backend
export async function getCart() {
  try {
    const response = await axios.get(`${base}/api/cart`, reqCfg());
    return response.data.cart.items;
  } catch (error) {
    if (error.response?.status === 401) {
      return guestCartParse();
    }
    console.error("Error fetching backend cart:", error);
    return guestCartParse();
  }
}

// Add or update item in cart
export async function addToCart(product, quantity) {
  try {
    const response = await axios.post(
      `${base}/api/cart/add`,
      {
        productId: product.productId,
        quantity: quantity,
      },
      reqCfg(),
    );
    return response.data.cart.items;
  } catch (error) {
    if (error.response?.status !== 401) {
      console.error("Failed to add to cart:", error);
      throw error;
    }
  }

  const cart = guestCartParse();
  const existingProductIndex = cart.findIndex((item) => item.productId === product.productId);

  if (existingProductIndex === -1) {
    cart.push({
      productId: product.productId,
      quantity: quantity,
      price: product.price,
      name: product.name,
      image: product.images[0],
    });
    localStorage.setItem("cart", JSON.stringify(cart));
  } else {
    const newQuantity = cart[existingProductIndex].quantity + quantity;
    if (newQuantity <= 0) {
      const newCart = cart.filter((item, index) => index !== existingProductIndex);
      localStorage.setItem("cart", JSON.stringify(newCart));
    } else {
      cart[existingProductIndex].quantity = newQuantity;
      localStorage.setItem("cart", JSON.stringify(cart));
    }
  }

  return await getCart();
}

// Calculate total price
export async function getTotal() {
  const cart = await getCart();
  let total = 0;
  cart.forEach((item) => {
    total += item.price * item.quantity;
  });
  return total;
}

// Remove item from cart
export async function removeFromCart(productId) {
  try {
    const response = await axios.delete(`${base}/api/cart/${productId}`, reqCfg());
    return response.data.cart.items;
  } catch (error) {
    if (error.response?.status !== 401) {
      console.error("Failed to remove item from cart:", error);
      throw error;
    }
  }

  const cart = guestCartParse();
  const newCart = cart.filter((item) => item.productId !== productId);
  localStorage.setItem("cart", JSON.stringify(newCart));
  return newCart;
}

// Merge local cart with backend cart (after login)
export async function mergeCartOnLogin() {
  try {
    const localCart = localStorage.getItem("cart");
    if (!localCart || localCart === "[]") {
      return;
    }
    const cart = JSON.parse(localCart);
    await axios.post(`${base}/api/cart/merge`, { cart }, reqCfg());
    localStorage.removeItem("cart");
  } catch (error) {
    console.error("Error merging cart on login:", error);
  }
}

// Clear cart on order placement
export async function clearCart() {
  try {
    const response = await axios.delete(`${base}/api/cart/clear`, reqCfg());
    console.log("Backend cart cleared:", response.data);
    return;
  } catch (error) {
    if (error.response?.status === 401) {
      localStorage.setItem("cart", "[]");
      console.log("Guest cart cleared from localStorage");
      return;
    }
    console.error("Failed to clear backend cart:", error);
    throw error;
  }
}
