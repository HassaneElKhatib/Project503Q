import { MdSendTimeExtension } from "react-icons/md";
import { Link } from "react-router-dom";

export default function AuthSection({ user, defaultImage }) {
  const displayName = user?.firstName || user?.name || "Account";

  if (user) {
    return (
      <div className="flex gap-5 justify-center items-center text-xl">
            <Link to="/orders" className="items-center justify-center gap-1 hover:text-black hidden md:flex">
              <MdSendTimeExtension className="mt-[3px]"/> 
              <h2 className="">Orders</h2>
            </Link>
            <Link to="/client/dashboard" className="flex gap-3 items-center justify-center">
              <img src={user?.image || defaultImage} className="w-[40px] h-[40px] rounded-full object-cover shadow-xl border-2 border-accent-hover"></img>
              <h1 className="font-serif mt-[4px]">{displayName}</h1>
            </Link>
          </div>
    )
  }else {
    return (
      <div className="text-xl font-serif flex gap-3">
          <Link to="/login" className="hover:text-black">
            Login
          </Link>
          <Link to="/register" className="hover:text-black">
            Sign up
          </Link>
        </div> 
    )
  }
   
}