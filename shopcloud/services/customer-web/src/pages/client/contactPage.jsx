import {
  FaEnvelope,
  FaPhoneAlt,
  FaMapMarkerAlt,
  FaInstagram,
  FaFacebookF,
  FaTiktok,
  FaWhatsapp,
} from "react-icons/fa";

export default function ContactUs() {
  return (
    <div className="flex justify-center pb-20 bg-primary">
      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-lg overflow-hidden mt-10 mx-2">
        
        {/* Header */}
        <div className="bg-accent-hover text-white text-center py-10">
          <h1 className="text-3xl font-bold font-serif">Contact ShopCloud</h1>
          <p className="mt-2 opacity-90 font-serif">
            We are here to help with your orders and account
          </p>
        </div>

        {/* Content */}
        <div className="p-8 grid md:grid-cols-2 gap-10 lg:gap-30">
          
          {/* Contact Details */}
          <div className="space-y-6 ml-15">
            <h2 className="text-xl font-semibold text-gray-800 ">
              Contact Information
            </h2>

            <a
              href="mailto:support@shopcloud.com"
              className="flex items-center gap-4 text-gray-700 hover:text-accent transition"
            >
              <FaEnvelope className="text-accent text-lg" />
              support@shopcloud.com
            </a>

            <a
              href="tel:+96181896694"
              className="flex items-center gap-4 text-gray-700 hover:text-accent transition"
            >
              <FaPhoneAlt className="text-accent text-lg" />
              +961 81 896 694
            </a>

            <div className="flex items-center gap-4 text-gray-700">
              <FaMapMarkerAlt className="text-accent text-lg" />
              Beirut, Lebanon
            </div>
          </div>

          {/* Social Media */}
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
              Follow Us
            </h2>

            <div className="flex gap-4">
              <a
                href="https://instagram.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-12 h-12 flex items-center justify-center rounded-full bg-amber-100 text-accent hover:bg-accent hover:text-white transition"
              >
                <FaInstagram size={30} />
              </a>

              <a
                href="https://facebook.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-12 h-12 flex items-center justify-center rounded-full bg-amber-100 text-accent hover:bg-accent hover:text-white transition"
              >
                <FaFacebookF size={25}/>
              </a>

              <a
                href="https://tiktok.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-12 h-12 flex items-center justify-center rounded-full bg-amber-100 text-accent hover:bg-accent hover:text-white transition"
              >
                <FaTiktok size={25}/>
              </a>

              <a
                href="https://wa.me/94771234567"
                target="_blank"
                rel="noopener noreferrer"
                className="w-12 h-12 flex items-center justify-center rounded-full bg-amber-100 text-accent hover:bg-accent hover:text-white transition"
              >
                <FaWhatsapp size={30} />
              </a>
            </div>

            <p className="text-sm text-gray-500">
              Reach out on your preferred platform for quick help.
            </p>
          </div>
        </div>
      </div>
    </div>  
  );
}
