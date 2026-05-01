import './App.css'
import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { mergeCartOnLogin } from './utils/cart'
import LoginPage from './pages/loginPage'
import RegisterPage from './pages/registerPage'
import AdminPage from './pages/adminPage'
import TestPage from './pages/testPage'
import { Toaster } from 'react-hot-toast'
import ClientHomePage from './pages/client/clientHomePage'
import ForgetPasswordPage from './pages/forgetPasswordPage'
import ResetPasswordPage from './pages/resetPasswordPage'
import { GoogleOAuthProvider } from '@react-oauth/google';
import ClientDashboard from './pages/clientDashboardPage'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      cacheTime: 1000 * 60 * 10,
      refetchOnWindowFocus: false,
      retry: 1,
    }
  }
});


function App() {
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "local-dev-disabled";

  useEffect(() => {
    mergeCartOnLogin();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <GoogleOAuthProvider clientId={googleClientId}>
          <div className="w-screen min-h-screen bg-primary text-secondary m-0 p-0">
              <Toaster position='top-right' reverseOrder={true} />
              <Routes path="/">
                <Route path="/login" element={<LoginPage />}/>
                <Route path="/admin/login" element={<LoginPage />}/>
                <Route path="/test" element={<TestPage />}/>
                <Route path="/register" element={<RegisterPage />}/>
                <Route path="/admin/*" element={<AdminPage />}/>
                <Route path="/forget-password" element={<ForgetPasswordPage />}/>
                <Route path="/reset-password" element={<ResetPasswordPage />}/>
                <Route path="/client/dashboard/*" element={<ClientDashboard />}/>
                <Route path="/*" element={<ClientHomePage />}/>
              </Routes>  
          </div> 
          </GoogleOAuthProvider> 
      </BrowserRouter>
      {/* <ReactQueryDevtools initialIsOpen={false} /> */}
    </QueryClientProvider>
  )
}

export default App
