import { Route, Routes } from "react-router-dom";
import Header from "../../components/Header";
import ProductsPage from "./productsPage";
import ProductOverviewPage from "./productOverviewPage";
import CartPage from "./cartPage";
import CheckoutPage from "./checkoutPage";
import OrderConfirmationPage from "./orderConfirmationPage";
import OrdersHistoryPage from "./ordersHistoryPage";
import ContactUs from "./contactPage";
import AboutUs from "./aboutUsPage";
import SiteReviews from "./siteReviewPage";
import HomePage from "./homePage";
import Footer from "../../components/Footer";


export default function ClientHomePage() {
  return (
    <div className="w-full h-screen">
      <Header />
      <Routes path="/">
        <Route path="/" element={<HomePage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/reviews" element={<SiteReviews />} />
        <Route path="/aboutUs" element={<AboutUs />} />
        <Route path="/contactUs" element={<ContactUs />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/overview/:productId" element={<ProductOverviewPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/order-confirmation" element={<OrderConfirmationPage />} />
        <Route path="/orders" element={<OrdersHistoryPage />} />
        <Route path="/*" element={<h1 className="text-center mt-10 text-3xl font-bold">404 - Page Not Found</h1>} />
      </Routes>
      <Footer />
    </div>
  )

}