import { Link } from "react-router-dom";

const FALLBACK_IMAGE =
  "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400'><rect width='100%25' height='100%25' fill='%23f3f4f6'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%239ca3af' font-family='Arial' font-size='24'>No image</text></svg>";

function resolveImageSrc(image) {
  if (!image) {
    return FALLBACK_IMAGE;
  }
  if (image.startsWith("http://") || image.startsWith("https://") || image.startsWith("data:image/")) {
    return image;
  }
  return image;
}

function formatUSD(value) {
  return Number(value || 0).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function ProductCard(props) {
  const product = props.product; 
  return (
    <Link to={"/overview/"+product.productId}
      className="w-[300px] h-[400px] flex flex-col shrink-0 shadow-xl rounded-2xl overflow-hidden bg-white transition-transform hover:scale-105 hover:shadow-2xl"
    >
      {/* Product Image */}
      <div className="w-full h-[250px] relative">
        <img
          src={resolveImageSrc(product.images?.[0])}
          alt={product.name}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = FALLBACK_IMAGE;
          }}
        />
        {product.labelledPrice > product.price && (
          <span className="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-lg shadow-md">
            SALE
          </span>
        )}
      </div>

      {/* Product Info */}
      <div className="w-full h-[150px] flex flex-col p-4">
        <div>
          <h1 className="text-lg font-bold leading-tight line-clamp-2">
            {product.name}{" "}
            <span className="text-gray-500 text-sm font-medium">
              ({product.category})
            </span>
          </h1>
        </div>

        {/* Price Section */}
        <div className="mt-auto flex items-center justify-between">
          {product.labelledPrice > product.price ? (
            <p className="text-base font-semibold">
              <span className="line-through mr-2 text-gray-400 text-sm">
                {formatUSD(product.labelledPrice)}
              </span>
              <span className="text-accent">
                {formatUSD(product.price)}
              </span>
            </p>
          ) : (
            <span className="text-green-600 font-semibold">
              {formatUSD(product.price)}
            </span>
          )}
          <span
            className={`text-xs font-semibold px-2 py-1 rounded-full ${
              Number(product.stock || 0) > 0
                ? "bg-emerald-50 text-emerald-700"
                : "bg-rose-50 text-rose-700"
            }`}
          >
            {Number(product.stock || 0) > 0
              ? `${Number(product.stock || 0)} in stock`
              : "Out of stock"}
          </span>
        </div>
      </div>
    </Link>
  );
}
