import React from "react";
import { Link } from "react-router-dom";

export default function HomePage() {
  const heroVideoRef = React.useRef(null);
  const clipStartSeconds = 2;
  const clipEndSeconds = 11;

  const handleVideoLoadedMetadata = () => {
    const video = heroVideoRef.current;
    if (!video) return;
    video.currentTime = clipStartSeconds;
  };

  const handleVideoTimeUpdate = () => {
    const video = heroVideoRef.current;
    if (!video) return;
    if (video.currentTime >= clipEndSeconds) {
      video.currentTime = clipStartSeconds;
      video.play().catch(() => {});
    }
  };

  const collections = [
    {
      name: "Electronics",
      emoji: "📱",
      description: "Smart devices and useful accessories selected for everyday performance."
    },
    {
      name: "Fashion",
      emoji: "👕",
      description: "Comfortable, modern styles for every taste and every season."
    },
    {
      name: "Home Essentials",
      emoji: "🏠",
      description: "Practical home picks that make daily life simpler and more organized."
    },
    {
      name: "Sports & Outdoor",
      emoji: "🏃",
      description: "Gear and accessories to help you stay active indoors and outdoors."
    }
  ]

  const topBrands = [
    {
      name: "Cedars Apothecary",
      icon: "🌿",
      description: "Reliable daily products with a focus on quality and great value."
    },
    {
      name: "Byblos Bloom",
      icon: "🍃",
      description: "Trendy lifestyle picks designed for modern homes and routines."
    },
    {
      name: "Beirut Blush",
      icon: "🪶",
      description: "Customer-loved essentials across fashion, tech, and personal use."
    },
    {
      name: "ShopCloud Select",
      icon: "🌱",
      description: "Our curated favorites combining quality, affordability, and fast delivery."
    }
  ];


  return (
    <div className="min-h-screen bg-primary pb-20 ">
      {/* HERO SECTION */}
      <div className="flex justify-center mb-8 px-4 sm:px-6 lg:px-8">
        <section className="h-auto min-h-[500px] sm:min-h-[600px] lg:h-[670px] w-full flex flex-col items-start relative">

          <video
            ref={heroVideoRef}
            src="https://videos.pexels.com/video-files/4058080/4058080-uhd_2732_1440_25fps.mp4"
            className="w-full h-full object-cover rounded-xl sm:rounded-2xl lg:rounded-3xl shadow-lg absolute top-0 left-0"
            autoPlay
            loop
            muted
            playsInline
            poster="/ecommerce-auth-bg.jpg"
            onLoadedMetadata={handleVideoLoadedMetadata}
            onTimeUpdate={handleVideoTimeUpdate}
          />

          <div className="relative z-10 w-full h-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-0 flex items-center">

          
            <div className="lg:ml-8">
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-4 sm:mb-6 font-serif text-white/90">
                Shop Smarter <br /> Every Day
              </h1>
              <p className="text-white/80 max-w-md mb-6 sm:mb-8 text-base sm:text-lg">
                Explore a wide range of products for all interests, styles, and
                needs in one place.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                <Link to="/products" className="px-6 py-3 rounded-md bg-accent hover:bg-accent-hover text-white transition text-center">
                  Shop Now
                </Link>
                <Link to="/aboutUs" className="px-6 py-3 rounded-md border border-white/50 hover:bg-white/10 text-white/80 transition text-center">
                  Learn More
                </Link>
              </div>
            </div>

          </div>
        </section>
      </div>

      {/* COLLECTION */}
      <section className="mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl mt-12 sm:mt-16 lg:mt-20">
        <h2 className="text-xl sm:text-2xl font-semibold mb-6 sm:mb-8 font-serif">Our Collections</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          {collections.map((item) => (
            <div
              key={item.name}
              className="rounded-xl bg-white shadow-sm hover:shadow-md transition p-6 text-center"
            >
              <div className="text-4xl mb-4">{item.emoji}</div>
              <h3 className="font-semibold mb-2 text-lg">{item.name}</h3>
              <p className="text-sm text-gray-600">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-accent-hover mt-12 sm:mt-16 lg:mt-20 text-white py-12 sm:py-16 lg:py-20 text-center px-4">
        <h2 className="text-2xl sm:text-3xl font-bold font-serif">Everything You Need, One Store</h2>
        <p className="mb-5 text-white/80 text-base sm:text-lg max-w-2xl mx-auto">
          Shop confidently with collections built for everyone.
        </p>
        <Link to="/products" className="inline-block px-6 sm:px-8 py-3 rounded-md bg-white text-accent hover:bg-gray-100 transition shadow-lg">
          Explore Products
        </Link>
      </section>

      {/* TOP BRANDS */}
      <section className="mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl mt-12 sm:mt-16 lg:mt-20">
        <h2 className="text-xl sm:text-2xl font-semibold mb-6 sm:mb-8 font-serif">Top Brands</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          {topBrands.map((item) => (
            <div
              key={item.name}
              className="rounded-xl bg-white shadow-sm hover:shadow-md transition p-6 text-center"
            >
              <div className="text-4xl mb-4">{item.icon}</div>
              <h3 className="font-semibold font-serif mb-2 text-lg">{item.name}</h3>
              <p className="text-sm text-gray-600">{item.description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}