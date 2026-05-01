import axios from "axios";

// Get cart from localStorage or backend
export async function getCart() {
  const token = localStorage.getItem("token"); 

  if (!token) {
    // for guest user, get cart from localStorage
    let cartInString = localStorage.getItem("cart");

    if (cartInString == null) {
      cartInString = "[]";
      localStorage.setItem("cart", cartInString);
    }

    const cart = JSON.parse(cartInString);
    return cart;

  } else {
    // for logged-in user, get cart from backend
    try {
      const response = await axios.get(import.meta.env.VITE_BACKEND_URL + "/api/cart", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      return response.data.cart.items;

    } catch (error) {
      console.error("Error fetching backend cart:", error);
      return [];
    }
  }
}

// Add or update item in cart
export async function addToCart(product, quantity) {
  const token = localStorage.getItem("token");

  if (!token) {
    const cart = await getCart(); 

    const existingProductIndex = cart.findIndex(
      (item) => item.productId === product.productId
    );

    if (existingProductIndex === -1) {
      // Add new item
      cart.push({
        productId: product.productId,
        quantity: quantity,
        price: product.price,
        name: product.name,
        image: product.images[0]
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

  } else {
    try {
      const response = await axios.post(import.meta.env.VITE_BACKEND_URL+"/api/cart/add",
        {
          productId: product.productId,
          quantity: quantity
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
     
      return response.data.cart.items;

    } catch (error) {
      console.error("Error adding items to backend cart:", error);
      throw error; 
    }
  }
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
  const token = localStorage.getItem("token");

  if (!token) {
    const cart = await getCart();
    const newCart = cart.filter(item => item.productId !== productId);
    localStorage.setItem("cart", JSON.stringify(newCart));
    return newCart;

  } else {
    try {
      const response = await axios.delete(
        `${import.meta.env.VITE_BACKEND_URL}/api/cart/${productId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      return response.data.cart.items;
    } catch (error) {
      console.error("Failed to remove item from cart:", error);
      throw error;
    }
  }
}

// Merge local cart with backend cart
export async function mergeCartOnLogin(token) {
  try {
    const localCart = localStorage.getItem("cart");
    
    if (!localCart || localCart === "[]") {
      return; 
    }

    const cart = JSON.parse(localCart);

    await axios.post(import.meta.env.VITE_BACKEND_URL + "/api/cart/merge",
      { cart },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    localStorage.removeItem("cart");

  } catch (error) {
    console.error("Error merging cart on login:", error);
  }
}

// Clear cart on order placement
export async function clearCart() {
  const token = localStorage.getItem("token");

  if (!token) {
    localStorage.setItem("cart", "[]");
    console.log("Guest cart cleared from localStorage");

  } else {
    try {
      const response = await axios.delete(import.meta.env.VITE_BACKEND_URL+"/api/cart/clear",
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      console.log("Backend cart cleared:", response.data);

    } catch (error) {

      console.error("Failed to clear backend cart:", error);
      throw error; // Re-throw so we know if it fails
    }
  }
}