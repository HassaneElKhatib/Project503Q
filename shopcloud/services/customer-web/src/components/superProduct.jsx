import ProductCard from "./productCard";

export default function SuperProduct() {
  return (
    <div className="bg-gray-50 min-h-screen py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-8">
          Feature This Week!
        </h1>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="mb-4">
            <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-medium">
              Featured
            </span>
          </div>
          
          <ProductCard 
            name="Samsung Galaxy S24 Ultra"
            image="https://picsum.photos/id/3/200/300"
            price="1900/="
          />
        </div>
      </div>
    </div>
  );
}