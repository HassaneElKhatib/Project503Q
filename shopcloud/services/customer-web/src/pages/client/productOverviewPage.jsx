import axios from "axios";
import { useEffect, useState } from "react";
import { publicApiOrigin } from "../../utils/publicApiOrigin";
import toast from "react-hot-toast";
import { useNavigate, useParams } from "react-router-dom";
import Loader from "../../components/loader";
import ImageSlider from "../../components/imageSlider";
import { addToCart } from "../../utils/cart";
import { ProductReview } from "../../components/review/productReviews";

function normalizeProduct(rawProduct) {
  if (!rawProduct || typeof rawProduct !== "object") {
    return null;
  }

  const rawPrice = rawProduct.price ?? rawProduct.price_cents ?? 0;
  const price = Number(rawProduct.price_cents != null ? Number(rawPrice) / 100 : rawPrice);
  const normalizedPrice = Number.isFinite(price) ? price : 0;
  const imageUrl = rawProduct.image_url || rawProduct.imageUrl;

  return {
    ...rawProduct,
    productId: rawProduct.productId ?? rawProduct.id ?? rawProduct.sku ?? "unknown-product",
    images: Array.isArray(rawProduct.images) ? rawProduct.images : (imageUrl ? [imageUrl] : []),
    labelledPrice: Number(rawProduct.labelledPrice ?? normalizedPrice),
    price: normalizedPrice,
    altNames: Array.isArray(rawProduct.altNames) ? rawProduct.altNames : [],
    category: rawProduct.category ?? "general",
  };
}

export default function ProductOverviewPage() {
  const navigate = useNavigate();
  const params = useParams();
  const[product, setProduct] = useState(null);
  const[status, setStatus] = useState("loading"); // loading, success, error
  const[reviews, setReviews] = useState([]);

  const productId = params.productId;

  useEffect(
    () => {

      if(status == "loading") {
        axios.get(`${publicApiOrigin()}/api/products/${productId}`,
        ).then(
          (res) => {
            const rawProduct = res.data?.product ?? res.data;
            const normalizedProduct = normalizeProduct(rawProduct);

            if (!normalizedProduct) {
              setStatus("error");
              toast.error("Failed to fetch product details.");
              return;
            }

            setProduct(normalizedProduct);
            setStatus("success");
          }
        ).catch(
          () => {
            setStatus("error");
            toast.error("Failed to fetch product details.");
          }
        )
      }
    }, [status]
  )

  useEffect(
    () => {
      axios.get(`${publicApiOrigin()}/api/reviews/product/${productId}`,
      ).then(
        (res) => {
          console.log(res.data.reviews);
          setReviews(res.data.reviews);
        }
      ).catch(
        () => {
          console.log("Failed to fetch reviews.");
        }
      )

    }, [params.productId]
  )

  return(
    <div className="w-full min-h-screen pb-12 sm:pb-16 lg:pb-20 bg-primary">
      {
        status == "loading" && <Loader />
      }
      {
        status == "success" && (
        <div className="px-4 sm:px-6 lg:px-12 xl:px-24 max-w-7xl mx-auto">
          <div className="w-full flex bg-white p-4 sm:p-6 lg:p-10 rounded-xl shadow-xl flex-col lg:flex-row">
            
            {/* Mobile Title */}
            <div className="lg:hidden px-4 flex justify-center items-center text-center mb-6">
              <h1 className="text-xl sm:text-2xl font-bold">
                {product.name}{" "}
                {product.altNames && product.altNames.length > 0 && (
                  <span className="font-light text-base sm:text-lg block mt-2">
                    {product.altNames.join(" | ")}
                  </span>
                )}
              </h1>
            </div>

            {/* Image Section */}
            <div className="w-full lg:w-1/2 flex flex-col justify-center items-center mb-8 lg:mb-0">
              <ImageSlider images={product.images} />
            </div>

            {/* Product Details Section */}
            <div className="w-full lg:w-1/2 flex flex-col justify-start items-center px-4 sm:px-6 lg:px-8 lg:mt-5">
              
              {/* Desktop Title */}
              <div className="hidden lg:block w-full text-center mb-6">
                <h1 className="text-2xl xl:text-3xl font-bold flex flex-col justify-center items-center">
                  {product.name}
                  <span className="font-light text-lg xl:text-xl mt-2">
                    {product.altNames.join(" | ")}
                  </span>
                </h1>
              </div>

              {/* Description */}
              <p className="text-base sm:text-lg lg:mt-6 text-center lg:text-left w-full">
                {product.description}
              </p>

              {/* Price Section */}
              <div className="w-full flex justify-center items-center mt-6 lg:mt-8">
                {
                  product.labelledPrice > product.price?
                  <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4">
                    <span className="text-2xl sm:text-3xl font-bold">
                      ${product.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span className="text-xl sm:text-2xl font-semibold line-through">
                      ${product.labelledPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                  :
                  <div>
                    <span className="text-2xl sm:text-3xl font-bold">
                      ${product.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                }
              </div>

              {/* Action Buttons */}
              <div className="w-full flex flex-col sm:flex-row justify-center items-center mt-8 lg:mt-12 gap-4">
                <button 
                  className="w-full sm:w-48 h-12 cursor-pointer rounded-xl shadow-2xl text-white bg-accent border-[3px] border-accent hover:bg-white hover:text-accent transition-all" 
                  onClick={
                    () => {
                      navigate("/checkout", 
                        {
                          state: { items: 
                            [{
                                productId: product.productId,
                                quantity: 1,
                                name: product.name,
                                image: product.images[0],
                                price: product.price
                            }]
                        }
                        });
                    }
                  }
                >
                  Buy Now
                </button>
                <button 
                  className="w-full sm:w-48 h-12 cursor-pointer rounded-xl shadow-2xl text-white bg-accent-hover border-[3px] border-accent-hover hover:bg-white hover:text-accent-hover transition-all" 
                  onClick={
                    async ()=> {
                      try{
                        await addToCart(product, 1);
                        toast.success("Product added to cart");

                      }catch(error){
                        console.log(error);
                        toast.error("Failed to add product to cart");
                      }
                    }
                  }
                >
                  Add to Cart
                </button>
              </div>
            </div>
          </div>

          {/* Reviews Section */}
          <div className="mt-12 sm:mt-16 lg:mt-20">
            <h1 className="text-2xl sm:text-3xl font-bold text-secondary mb-6 sm:mb-8">
              Customer Reviews
            </h1>
            <ProductReview reviews={reviews} />
          </div>
        </div>
      )
      }
      {
        status == "error" && (
          <div className="flex justify-center items-center min-h-[400px]">
            <div className="text-center px-4">
              <p className="text-xl text-red-600">Product fetching error</p>
            </div>
          </div>
        )
      }
    </div>
  )
}