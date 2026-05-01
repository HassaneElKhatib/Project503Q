<p align="center">
  <img src="/public/readmelogo.png" alt="Faye Beauty Logo" width="400"/>
</p>

<h1 align="center">💄 Faye Beauty</h1>

<p align="center">
  <em>A premium cosmetics e-commerce experience - beautifully designed, blazing fast.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19.1-61DAFB?style=for-the-badge&logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/Vite-7.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-4.1-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS"/>
  <img src="https://img.shields.io/badge/Node.js-Express-339933?style=for-the-badge&logo=node.js&logoColor=white" alt="Node.js"/>
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/>
</p>

<p align="center">
  <a href="https://faybeauty-frontend-yigo.vercel.app">🌐 Live Demo</a> •
  <a href="#-features">✨ Features</a> •
  <a href="#-tech-stack">🧰 Tech Stack</a> •
  <a href="#-getting-started">🚀 Getting Started</a> •
  <a href="#-screenshots">📸 Screenshots</a>
</p>

---

## 📖 About the Project

**Faye Beauty** is a modern, full-stack cosmetics e-commerce web application built to deliver a smooth, intuitive, and visually stunning shopping experience. It enables users to explore beauty products, view detailed product information, read & write reviews, manage their cart, and place orders securely - all powered by a robust REST API backend.

The platform includes a comprehensive **Admin Dashboard** with real-time analytics, product management, order tracking, user management, and review moderation - giving store administrators complete control over their cosmetics business.

---

## 🌐 Live Demo

| Service   | URL                                                      |
| --------- | -------------------------------------------------------- |
| 🖥️ Frontend | [faybeauty-frontend-yigo.vercel.app](https://faybeauty-frontend-yigo.vercel.app) |
| 🔗 Backend API | [faybeauty-backend-api.onrender.com](https://faybeauty-backend-api.onrender.com) |

> **Note:** The backend is hosted on Render's free tier, so the first request may take ~30 seconds to wake up the server.

---

## ✨ Features

### 🛍️ Customer Experience
| Feature | Description |
| ------- | ----------- |
| 🏠 Dynamic Home Page | Hero section with image slider, featured products, and site reviews |
| 📦 Product Browsing | Browse products by categories with pagination support |
| 🔍 Product Details | Detailed product overview with images, pricing, and customer reviews |
| 🛒 Smart Cart | Add, update quantity, remove products with persistent cart state |
| 💳 Secure Checkout | Complete order placement with shipping details |
| 📜 Order History | Track all past orders with detailed status and order cancellation |
| ⭐ Product Reviews | Rate and review products you've purchased |
| 💬 Site Reviews | Share your overall experience with the platform |
| 📞 Contact & About | Informational pages for customer support and brand story |

### 🛠️ Admin Dashboard
| Feature | Description |
| ------- | ----------- |
| 📊 Analytics Dashboard | Visual sales & order insights with interactive charts (Recharts) |
| 📦 Product Management | Full CRUD — Add, Update, Delete products with image uploads |
| 📋 Order Management | View, process, and manage all customer orders |
| 👥 User Management | View and manage registered users |
| ⭐ Review Moderation | Monitor and manage product and site reviews |
| ⚙️ Admin Settings | Configure admin profile and account settings |

### 🔐 Authentication & Security
| Feature | Description |
| ------- | ----------- |
| 📧 Email & Password | Traditional registration with email verification via OTP |
| 🔑 Google OAuth | One-click sign-in with Google |
| 🎫 JWT Authorization | Secure, token-based session management |
| 🔒 Password Recovery | Forgot password flow with email-based reset |
| 🛡️ Role-Based Access | Admin vs. Customer role separation |

---

## 🧰 Tech Stack

### Frontend
| Technology | Purpose |
| ---------- | ------- |
| [React 19](https://react.dev/) | UI library with latest features |
| [Vite 7](https://vitejs.dev/) | Next-gen build tool for fast dev experience |
| [Tailwind CSS 4](https://tailwindcss.com/) | Utility-first CSS framework |
| [React Query (TanStack)](https://tanstack.com/query) | Server state management, caching & synchronization |
| [React Router 7](https://reactrouter.com/) | Client-side routing |
| [Axios](https://axios-http.com/) | HTTP client for API communication |
| [Recharts](https://recharts.org/) | Data visualization for admin dashboard |
| [React Hot Toast](https://react-hot-toast.com/) | Beautiful toast notifications |
| [React Icons](https://react-icons.github.io/react-icons/) | Icon library |
| [Day.js](https://day.js.org/) | Lightweight date utility |
| [Supabase](https://supabase.com/) | Media storage (product image uploads) |

### Backend
| Technology | Purpose |
| ---------- | ------- |
| Node.js | Server runtime |
| Express.js | Web framework |
| MongoDB (Mongoose) | Database & ODM |
| JWT | Token-based authentication |
| Google OAuth | Third-party authentication |
| Nodemailer | Email verification & OTP delivery |

### Deployment
| Service | Purpose |
| ------- | ------- |
| [Vercel](https://vercel.com/) | Frontend hosting with CI/CD |
| [Render](https://render.com/) | Backend API hosting |
| [MongoDB Atlas](https://www.mongodb.com/atlas) | Cloud database |
| [Supabase](https://supabase.com/) | File/media storage |

---

## � Architecture Highlights

```
┌────────────┐     HTTPS      ┌────────────┐     Mongoose     ┌────────────┐
│            │  ◄──────────►  │            │  ◄────────────►  │            │
│  React SPA │     REST API   │  Express   │                  │  MongoDB   │
│  (Vercel)  │                │  (Render)  │                  │  (Atlas)   │
│            │                │            │                  │            │
└────────────┘                └────────────┘                  └────────────┘
       │                            │
       │                            │
       ▼                            ▼
  ┌──────────┐               ┌──────────────┐
  │ Supabase │               │  Nodemailer  │
  │ Storage  │               │  (Email/OTP) │
  └──────────┘               └──────────────┘
```

- **RESTful API** design with clean endpoint patterns
- **Modular MVC** backend architecture
- **React Query** for efficient server-state caching, background refetching & optimistic updates
- **Custom hooks** for encapsulated data-fetching logic (`useUserQueries`, `useOrderQueries`, `useReviewQueries`, etc.)
- **Service layer pattern** separating API calls from UI logic
- **Role-based access control** with JWT token validation
- **Scalable MongoDB** schema design with Mongoose

---

## 📂 Project Structure

```
skyrek-frontend/
├── public/
│   ├── screenshots/          # README screenshot assets
│   └── ...                   # Static assets (logo, images)
│
├── src/
│   ├── api/                  # API route definitions
│   │   └── productApi.js     # Product API endpoints
│   │
│   ├── assets/               # Images, icons, static assets
│   │
│   ├── components/           # Reusable UI components
│   │   ├── Header.jsx        # Navigation header
│   │   ├── Footer.jsx        # Site footer
│   │   ├── Card.jsx          # Product card component
│   │   ├── productCard.jsx   # Product listing card
│   │   ├── imageSlider.jsx   # Hero image carousel
│   │   ├── paginator.jsx     # Pagination component
│   │   ├── loader.jsx        # Loading spinner
│   │   ├── review/           # Review-related components
│   │   └── ...
│   │
│   ├── config/               # App & environment config (Axios instance)
│   │
│   ├── hooks/                # Custom React hooks
│   │   ├── useDashboardQueries.js
│   │   ├── useOrderQueries.js
│   │   ├── useReviewQueries.js
│   │   ├── useSiteReviewQueries.js
│   │   └── useUserQueries.js
│   │
│   ├── pages/                # Application pages
│   │   ├── admin/            # Admin panel pages
│   │   │   ├── dashboardAdminPage.jsx
│   │   │   ├── productsAdminPage.jsx
│   │   │   ├── addProductAdminPage.jsx
│   │   │   ├── updateProductPage.jsx
│   │   │   ├── ordersAdminPage.jsx
│   │   │   ├── userManagementPage.jsx
│   │   │   ├── reviewsManagementPage.jsx
│   │   │   └── settingAdminPage.jsx
│   │   │
│   │   ├── client/           # Customer-facing pages
│   │   │   ├── homePage.jsx
│   │   │   ├── productsPage.jsx
│   │   │   ├── productOverviewPage.jsx
│   │   │   ├── cartPage.jsx
│   │   │   ├── checkoutPage.jsx
│   │   │   ├── ordersHistoryPage.jsx
│   │   │   ├── aboutUsPage.jsx
│   │   │   ├── contactPage.jsx
│   │   │   ├── siteReviewPage.jsx
│   │   │   └── dashboard/
│   │   │
│   │   ├── loginPage.jsx
│   │   ├── registerPage.jsx
│   │   ├── forgetPasswordPage.jsx
│   │   └── resetPasswordPage.jsx
│   │
│   ├── services/             # API service functions
│   │   ├── authService.js
│   │   ├── dashboardService.js
│   │   ├── orderService.js
│   │   ├── reviewService.js
│   │   ├── siteReviewService.js
│   │   └── userService.js
│   │
│   ├── utils/                # Helper & utility functions
│   │   ├── cart.js           # Cart state management
│   │   ├── dayjs.js          # Date formatting config
│   │   ├── isAdmin.js        # Admin role check
│   │   ├── logout.js         # Logout handler
│   │   └── mediaUpload.jsx   # Supabase media upload
│   │
│   ├── App.jsx               # Root application component
│   ├── main.jsx              # Application entry point
│   ├── App.css               # Global styles
│   └── index.css             # Tailwind directives
│
├── .env                      # Environment variables
├── index.html                # HTML entry point
├── package.json              # Dependencies & scripts
├── vite.config.js            # Vite configuration
├── vercel.json               # Vercel deployment config
└── eslint.config.js          # ESLint configuration
```

---

## 📸 Screenshots

### 🏠 Home Page
![Home Page](/public/screenshots/home.png)

### 📦 Product Listing
![Products](/public/screenshots/products.png)

### 📊 Admin Dashboard
![Admin Dashboard](/public/screenshots/adminDashboard.png)

### 👤 Admin Profile Management
![Admin Profile](/public/screenshots/profile.png)

### 🛒 Shopping Cart
![Cart](/public/screenshots/cart.png)

---

## 🚀 Getting Started

Follow these steps to run the Faye Beauty frontend locally.

### Prerequisites

Make sure you have the following installed:

- **Node.js** >= 18.x — [Download](https://nodejs.org/)
- **npm** >= 9.x (comes with Node.js)
- **Git** — [Download](https://git-scm.com/)

### 📥 Clone the Repository

```bash
git clone https://github.com/chamod-malindu/faybeauty-frontend.git
cd faybeauty-frontend
```

### 📦 Install Dependencies

```bash
npm install
```

### ⚙️ Environment Variables Setup

Create a `.env` file in the project root:

```env
VITE_BACKEND_URL=https://faybeauty-backend-api.onrender.com
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_GOOGLE_CLIENT_SECRET=your_google_client_secret
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

| Variable | Description |
| -------- | ----------- |
| `VITE_BACKEND_URL` | URL of the backend REST API |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth Client ID from Google Cloud Console |
| `VITE_GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret |
| `VITE_SUPABASE_URL` | Supabase project URL for media storage |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key for client-side access |

### ▶️ Run the Development Server

```bash
npm run dev
```

The application will be available at: **http://localhost:5173**

### 🏗️ Build for Production

```bash
npm run build
npm run preview
```

---

## 🔗 API Endpoints Overview

The frontend communicates with the following REST API endpoint groups:

| Endpoint Group | Methods | Description |
| -------------- | ------- | ----------- |
| `/api/auth` | POST | Register, Login, Verify OTP, Forgot/Reset Password |
| `/api/products` | GET, POST, PUT, DELETE | Product CRUD operations |
| `/api/orders` | GET, POST, PUT | Order placement & management |
| `/api/reviews` | GET, POST, PUT, DELETE | Product review operations |
| `/api/site-reviews` | GET, POST, PUT, DELETE | Site-wide review operations |
| `/api/users` | GET, PUT, DELETE | User management (Admin) |
| `/api/dashboard` | GET | Dashboard analytics data |

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push** to your branch
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open** a Pull Request

---

## 🌟 Future Enhancements

- [ ] Wishlist functionality
- [ ] Advanced search with filters (price range, brand, category)
- [ ] Payment gateway integration (Stripe / PayPal)
- [ ] Real-time order status notifications
- [ ] Multi-language support (i18n)
- [ ] Dark mode toggle
- [ ] Email marketing & newsletter subscription
- [ ] Inventory management for admins
- [ ] Product comparison feature

---

## 👨‍💻 Author

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/chamod-malindu">
        <img src="https://github.com/chamod-malindu.png" width="100px;" alt="Chamod Malindu"/>
        <br />
        <sub><b>Chamod Malindu</b></sub>
      </a>
      <br />
      <sub>BICT Undergraduate</sub>
      <br />
      <sub>Uva Wellassa University of Sri Lanka</sub>
      <br />
      <sub>Full Stack Developer</sub>
    </td>
  </tr>
</table>

---

<p align="center">
  <a href="#-faye-beauty">⬆️ Back to Top</a>
</p>
