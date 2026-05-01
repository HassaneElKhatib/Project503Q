# UI integration & gap matrix

The customer-web SPA was vendored from
[`chamod-malindu/faybeauty-frontend`](https://github.com/chamod-malindu/faybeauty-frontend).
It expects a single MERN-style backend; ShopCloud is AWS-native, so the
**api-gateway** service translates the SPA's REST contract onto the
underlying microservices and fills in the gaps.

## Endpoint mapping

| SPA call (axios)                  | api-gateway route                | Backed by                          | Status         |
| --------------------------------- | -------------------------------- | ---------------------------------- | -------------- |
| `POST /api/users`                 | `users.register`                 | gateway DB (bcrypt+JWT)            | ✅ implemented |
| `POST /api/users/login`           | `users.login`                    | gateway DB (bcrypt+JWT)            | ✅ implemented |
| `POST /api/users/google-login`    | `users.google_login`             | stub (501 in dev; Cognito in prod) | ⚠ stubbed      |
| `GET /api/users/me/`              | `users.get_me`                   | gateway DB                         | ✅ implemented |
| `PUT /api/users/`                 | `users.update_me`                | gateway DB                         | ✅ implemented |
| `POST /api/auth/forgot-password`  | `auth_recovery.forgot_password`  | gateway DB + in-mem code           | ⚠ dev-only flow (returns code in body) |
| `POST /api/auth/reset-password`   | `auth_recovery.reset_password`   | gateway DB                         | ✅ implemented |
| `GET /api/products`               | `products.list_products`         | catalog (httpx) → fallback gateway DB | ✅ implemented |
| `GET /api/products/:id`           | `products.get_product`           | gateway DB                         | ✅ implemented |
| `POST/PUT/DELETE /api/products`   | `products.create/update/delete`  | gateway DB (admin only)            | ✅ implemented |
| `GET /api/cart`                   | `cart.get_cart`                  | gateway DB                         | ✅ implemented |
| `POST /api/cart/add`              | `cart.add_to_cart`               | gateway DB                         | ✅ implemented |
| `DELETE /api/cart/:productId`     | `cart.remove_from_cart`          | gateway DB                         | ✅ implemented |
| `POST /api/cart/merge`            | `cart.merge_cart`                | gateway DB                         | ✅ implemented |
| `DELETE /api/cart/clear`          | `cart.clear_cart`                | gateway DB                         | ✅ implemented |
| `GET /api/orders/:page/:limit`    | `orders.list_orders`             | gateway DB                         | ✅ implemented |
| `POST /api/orders`                | `orders.create_order`            | gateway DB + best-effort checkout fan-out | ✅ implemented |
| `PUT /api/orders/:id`             | `orders.update_order_status`     | gateway DB                         | ✅ implemented |
| `GET /api/reviews/product/:id`    | `reviews.list_for_product`       | gateway DB                         | ✅ implemented |
| `GET /api/reviews/user`           | `reviews.list_for_user`          | gateway DB                         | ✅ implemented |
| `GET /api/reviews`                | `reviews.list_all`               | gateway DB (admin only)            | ✅ implemented |
| `POST /api/reviews`               | `reviews.create_review`          | gateway DB                         | ✅ implemented |
| `PUT/DELETE /api/reviews/:id`     | `reviews.update/delete_review`   | gateway DB                         | ✅ implemented |
| `GET/POST/PUT /api/site-reviews`  | `site_reviews.*`                 | gateway DB                         | ✅ implemented |
| `GET /api/dashboard`              | `dashboard.admin_dashboard`      | gateway DB aggregates              | ✅ implemented |
| `GET /api/dashboard/client`       | `dashboard.client_dashboard`     | gateway DB                         | ✅ implemented |

Every UI feature works end-to-end locally except Google sign-in (which
needs a real `VITE_GOOGLE_CLIENT_ID` and Cognito federation in prod) and
Supabase media uploads on the admin product create form (the SPA still
posts the URL field directly when no Supabase keys are set).

## How auth tokens flow

```
React (axios)
  └── Authorization: Bearer <jwt>        # set by config/axiosConfig.js
          │
          ▼
api-gateway
  ├── /api/users/login   ──► issues HS256 JWT (sub=userId, role=user|admin)
  ├── all other /api/*   ──► validates header, attaches claims to handler
          │
          ▼
upstream services (when configured)
  └── x-user-id, x-user-email, x-user-role headers forwarded on proxy calls
```

In production, swap `JWT_SECRET` for an RS256 key sourced from Secrets
Manager and have the api-gateway re-sign or proxy Cognito-issued tokens
to downstream services. The `auth` service already verifies Cognito JWTs
directly when callers bypass the gateway.

## Production migration path

When you're ready to retire the gateway-owned implementations:

1. **Users / auth**: point `users.login` and `users.register` at Cognito
   `InitiateAuth` + `SignUp` instead of the local SQLite store. Keep
   `/api/users/me/` as a Cognito ID-token decode.
2. **Products**: set `CATALOG_BASE_URL=http://catalog` in production
   compose/manifests; the gateway already prefers the upstream when it's
   reachable. Move admin CRUD into a new catalog write endpoint.
3. **Cart**: replace gateway cart routes with proxies to the cart
   service (Redis-backed). The schema is already compatible.
4. **Orders**: replace gateway orders routes with proxies to checkout
   for writes and admin for reads. Ensure idempotency keys are
   forwarded.
5. **Reviews / site-reviews**: build a new `reviews` microservice owned
   by Person C with its own RDS table; mirror the gateway routes.
6. **Dashboard**: aggregate from a read replica or a small materialized
   view; the gateway's in-process aggregation is intentionally simple.

The gateway's intent is short-lived: it lets the React UI exercise the
full app while the production-grade auth and orders flows are wired up.

## Frontend-only customizations

The vendored repo has one bug fixed in this tree:
`src/utils/cart.js` had a stray `y` after `return response.data.cart.items;`
which broke the file. The fix is the only divergence from upstream.

Adding new UI features:

- API calls live under `src/api/`; they all import the shared axios
  instance from `src/config/axiosConfig.js`, so they automatically hit
  the gateway.
- Custom React Query hooks (in `src/hooks/`) wrap the api functions for
  caching/refetching.
- Pages register routes in `src/App.jsx`.
