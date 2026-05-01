import axios from "axios";
import { useEffect, useState } from "react";
import { publicApiOrigin } from "../../utils/publicApiOrigin";
import Loader from "../../components/loader";
import ProduactCard from "../../components/productCard";

function normalizeProduct(product) {
  const rawPrice = product.price ?? product.price_cents ?? 0;
  const price = Number(product.price_cents != null ? Number(rawPrice) / 100 : rawPrice);
  const normalizedPrice = Number.isFinite(price) ? price : 0;

  return {
    ...product,
    productId: product.productId ?? product.id ?? product.sku ?? "unknown-product",
    images: Array.isArray(product.images) ? product.images : [],
    labelledPrice: Number(product.labelledPrice ?? normalizedPrice),
    price: normalizedPrice,
    category: product.category ?? "general",
  };
}

export default function ProductsPage() {
  const[products, setProduct] = useState([]);
  const[isLoading, setIsLoading] = useState(true);
  const[query, setQuery] = useState("");

  useEffect(
    () => {
      if(isLoading){
        axios.get(`${publicApiOrigin()}/api/products`).then(
          (res)=> {
            const rawProducts = res.data?.products ?? res.data?.items ?? [];
            const normalizedProducts = Array.isArray(rawProducts)
              ? rawProducts.map(normalizeProduct)
              : [];

            const trimmedQuery = query.trim().toLowerCase();
            const filteredProducts = trimmedQuery
              ? normalizedProducts.filter((product) =>
                  (product.name || "").toLowerCase().includes(trimmedQuery) ||
                  (product.category || "").toLowerCase().includes(trimmedQuery) ||
                  (product.productId || "").toLowerCase().includes(trimmedQuery)
                )
              : normalizedProducts;

            setProduct(filteredProducts);
            setIsLoading(false);
        }).catch(() => {
          setProduct([]);
          setIsLoading(false);
        })
      }
    },
    [isLoading]
)
  return (
    <div className="w-full min-h-screen bg-primary pb-10">
      <div className="w-full mb-[30px] mt-[30px] flex justify-center items-center px-3">
        <input type="text" placeholder="Search Products......." value={query} onChange={
          (e) => {
            setQuery(e.target.value);
            setIsLoading(true);
          }
        }
        className="w-[400px] h-[40px] border-accent border-2 rounded-xl p-2"></input>
      </div>
      {
        isLoading ? (
          <Loader />
        ) : (
          <div className="w-full flex flex-wrap items-center justify-center gap-[30px]">
            {products.length > 0 ? (
              products.map((product) => (
                <ProduactCard key={product.productId} product={product} />
              ))
            ) : query ? (
              <p className="text-accent text-lg mt-6">
                No products found for "{query}".
              </p>
            ) : (
              <p className="text-accent text-lg mt-6">
                No products available yet. Please check back later.
              </p>
            )}
          </div>
        )
      }
    </div>
  );
}