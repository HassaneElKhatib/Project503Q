import {
  FaLeaf,
  FaHeart,
  FaGlobe,
  FaStar,
} from "react-icons/fa";

export default function AboutUs() {
  return (
    <div className="flex justify-center py-12 bg-primary">
      <div className="max-w-5xl w-full bg-white rounded-2xl shadow-lg overflow-hidden">

        {/* Header */}
        <div className="bg-accent-hover text-white text-center py-12">
          <h1 className="text-4xl font-bold font-serif">About ShopCloud</h1>
          <p className="mt-3 opacity-90 font-serif max-w-2xl mx-auto">
            A modern e-commerce destination built for every customer
          </p>
        </div>

        {/* About Content */}
        <div className="p-10 space-y-12">

          {/* Intro */}
          <section className="text-center max-w-3xl mx-auto">
            <h2 className="text-2xl font-semibold text-gray-800 font-serif mb-4">
              Our Story
            </h2>
            <p className="text-gray-600 leading-relaxed">
              ShopCloud was built to make online shopping easy, reliable, and
              inclusive. We bring together practical essentials and trending
              products so everyone can find what fits their needs and style.
            </p>
          </section>

          {/* Values */}
          <section className="grid md:grid-cols-3 gap-8 text-center">
            
            <div className="p-6 rounded-xl bg-slate-50 shadow-lg hover:shadow-xl">
              <FaLeaf className="text-accent-hover text-3xl mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Curated Quality
              </h3>
              <p className="text-gray-600 text-sm">
                We choose products based on quality, usefulness, and trusted
                customer value.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-slate-50 shadow-lg hover:shadow-xl">
              <FaHeart className="text-accent-hover text-3xl mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Customer First
              </h3>
              <p className="text-gray-600 text-sm">
                Fast support, secure checkout, and a smooth shopping experience
                are at the center of every order.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-slate-50 shadow-lg hover:shadow-xl">
              <FaGlobe className="text-accent-hover text-3xl mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Made for Everyone
              </h3>
              <p className="text-gray-600 text-sm">
                Inclusive shopping for all genders, preferences, and lifestyles.
              </p>
            </div>

          </section>

          {/* Mission */}
          <section className="bg-slate-50 rounded-xl p-8 text-center">
            <h2 className="text-2xl font-semibold text-gray-800 font-serif mb-3">
              Our Mission
            </h2>
            <p className="text-gray-600 leading-relaxed max-w-3xl mx-auto">
              Our mission is to make e-commerce simple and dependable by
              offering variety, quality, and convenience in one trusted platform.
            </p>
          </section>

          {/* Trust */}
          <section className="text-center">
            <FaStar className="text-accent-hover text-4xl mx-auto mb-4" />
            <p className="text-gray-700 font-medium">
              Trusted by shoppers across Lebanon
            </p>
          </section>

        </div>
      </div>
    </div>
  );
}
