import { useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { handleRegister } from "../services/authService";

export default function RegisterPage() {
  const navigate = useNavigate();
  const authBackgroundImage =
    "/ecommerce-auth-bg.jpg";
  const[formData, setFormData] = useState(
    {
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      confirmPassword: "",
      phone: "",
      role: "user"
    }
  );

  function handleChange(e) {
    const name = e.target.name;
    const value = e.target.value;

    setFormData(
      {
        ...formData, // keep the other value same
        [name]: value // only update the value that changed
      }
    );
  }

  const register = async (e) => {

    e.preventDefault(); // prevent form submission from reloading the page

    if(!formData.password || !formData.confirmPassword){
      toast.error("Please fill in both password fields");
      return;
    }

    if(formData.password != formData.confirmPassword){
      toast.error("Passwords do not match");
      return;
    }

    try{
      const fullName = `${formData.firstName} ${formData.lastName}`.trim();
      const response = await handleRegister({
        name: fullName,
        email: formData.email,
        password: formData.password,
      });

      if(response) {
        navigate("/login");
      }

    }catch(error){
      console.log(error);
      toast.error(error.response.data.message || "Registration failed!" );
    }
  }  

  return (
    <div
      className="w-full h-screen bg-cover bg-center flex justify-center items-center"
      style={{ backgroundImage: `url(${authBackgroundImage})` }}
    >
      <div className="w-screen m-2 lg:w-[500px] lg:h-[500px] flex flex-col justify-center items-center backdrop-blur-sm shadow-2xl rounded-[30px]">
        {/* Title */}
        <h1 className="font-semibold font-serif text-3xl lg:text-5xl mt-[15px] mb-[20px] text-accent">Register</h1>

        <form onSubmit={register} className="lg:w-[450px] flex justify-center items-center flex-col  gap-4">
          <div className="grid lg:grid-cols-2 gap-4 w-full">
            <div>
              <label className="font-semibold text-accent-hover text-[17px]">First Name</label>
              <input 
                name="firstName"
                type="text"
                placeholder="First Name"
                value={formData.firstName}
                onChange={handleChange}
                required
                className="w-full h-[50px] border border-accent-hover text-white rounded-xl pl-[5px] focus:pl-[5px]"
              />
            </div>
            <div>
              <label className="font-semibold text-accent-hover text-[17px]">Last Name</label>
              <input 
                name="lastName"
                type="text"
                placeholder="Last Name"
                value={formData.lastName}
                onChange={handleChange}
                required
                className="w-full h-[50px] border border-accent-hover text-white rounded-xl pl-[5px] focus:pl-[5px]"
              />
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-4 w-full">
            <div className="flex flex-col">
              <label className="font-semibold text-accent-hover text-[17px]">Email</label>
              <input 
                name="email"
                type="text"
                placeholder="eg: example@email.com"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full h-[50px] border border-accent-hover text-white rounded-xl pl-[5px] focus:pl-[5px]"
              />
            </div>
            <div>
              <label className="font-semibold text-accent-hover text-[17px]">Contact Number</label>
              <input 
                name="phone"
                type="text"
                placeholder="+94700000000"
                value={formData.phone}
                onChange={handleChange}
                required
                className="w-full h-[50px] border border-accent-hover text-white rounded-xl pl-[5px] focus:pl-[5px]"
              />
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-4 w-full">
            <div className="flex flex-col">
              <label className="font-semibold text-accent-hover text-[17px]">Password</label>
              <input 
                name="password"
                type="password"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full h-[50px] border border-accent-hover text-white rounded-xl pl-[5px] focus:pl-[5px]"
              />
            </div>
            <div>
              <label className="font-semibold text-accent-hover text-[17px]">Confirm Password</label>
              <input 
                name="confirmPassword"
                type="password"
                placeholder="Reenter the pasword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                className="w-full h-[50px] border border-accent-hover text-white rounded-xl pl-[5px] focus:pl-[5px]"
              />
            </div>
          </div>

          <button type="submit" className="w-[200px] font-semibold bg-accent-hover hover:bg-accent h-[50px] rounded-xl">
            Register Now
          </button>
        </form>
      </div>
    </div>
  )
}
