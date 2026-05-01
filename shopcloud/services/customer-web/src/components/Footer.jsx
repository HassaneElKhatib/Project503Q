import React from "react";
import { FaFacebookF, FaInstagram, FaTiktok, FaWhatsapp } from "react-icons/fa";
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="bg-accent">
      <div className="max-w-7xl mx-auto px-6 py-16 grid gap-10 md:grid-cols-4">
        
        {/* Brand */}
        <div>
          <h3 className="text-xl font-bold mb-4 text-white font-serif">ShopCloud</h3>
          <p className="text-xs text-white/70 mb-2">Your all-in-one online store</p>
          <p className="text-sm text-white/80 leading-relaxed">
            Discover trusted products across categories, from daily essentials
            to trending picks for every lifestyle.
          </p>
        </div>

        {/* Shop */}
        <div className="lg:ml-5">
          <h4 className="font-semibold mb-4 text-white font-serif">Shop</h4>
          <ul className="space-y-2 text-sm text-white/80">
            <li className="hover:text-[#0f2d1d] cursor-pointer">Electronics</li>
            <li className="hover:text-[#0f2d1d] cursor-pointer">Home Essentials</li>
            <li className="hover:text-[#0f2d1d] cursor-pointer">Fashion</li>
            <li className="hover:text-[#0f2d1d] cursor-pointer">New Arrivals</li>
          </ul>
        </div>

        {/* Company */}
        <div>
          <h4 className="font-semibold mb-4 text-white font-serif">Company</h4>
          <ul className="space-y-2 text-sm text-white/80">
            <li className="hover:text-[#0f2d1d] cursor-pointer">
              <Link to="/aboutUs">About Us</Link>
            </li>
            <li className="hover:text-[#0f2d1d] cursor-pointer">
              <Link to="/contactUs">Contact</Link>
            </li>
            <li className="hover:text-[#0f2d1d] cursor-pointer">Privacy Policy</li>
            <li className="hover:text-[#0f2d1d] cursor-pointer">Terms of Service</li>
          </ul>
        </div>

        {/* Newsletter */}
        <div>
          <h4 className="font-semibold mb-4 text-white font-serif">Stay Connected</h4>
          <div className="flex gap-4 mb-5">
            <a
              href="https://instagram.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex text-white items-center justify-center rounded-full hover:text-black ransition"
            >
              <FaInstagram size={20} />
            </a>

            <a
              href="https://facebook.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex text-white items-center justify-center rounded-full hover:text-black ransition"
            >
              <FaFacebookF size={20}/>
            </a>

            <a
              href="https://tiktok.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex text-white items-center justify-center rounded-full hover:text-black ransition"
            >
              <FaTiktok size={20}/>
            </a>

            <a
              href="https://wa.me/94771234567"
              target="_blank"
              rel="noopener noreferrer"
              className="flex text-white items-center justify-center rounded-full hover:text-black ransition"
            >
              <FaWhatsapp size={20} />
            </a>
          </div>
          <Link to="/contactUs" className="text-accent text-sm bg-white px-4 py-2 rounded-md inline-block shadow-lg hover:text-white hover:bg-accent-hover transition">
            Contact Us
          </Link>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/50 py-6 text-center text-sm text-white/80">
        © {new Date().getFullYear()} ShopCloud. All rights reserved.
      </div>
    </footer>
  );
}
