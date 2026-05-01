# ShopCloud

A unified mono-repo combining the work of three teammates into a single
production-ready e-commerce platform with a vendored React/Vite UI.

```
shopcloud/
├── docker-compose.yml           # Local stack (postgres + redis + every service)
├── pyproject.toml               # Shared shopcloud-libs package
├── alembic.ini                  # DB migration config (Person C)
├── libs/                        # Shared Python libs (logger, JWT, AWS, DB) — Person A
├── migrations/                  # Alembic versions — Person C
├── manifests/                   # Kubernetes manifests — Person B (consumed by all)
├── infra/
│   ├── bootstrap/               # State bucket + DynamoDB lock table — Person C
│   └── envs/{dev,prod}/         # Env-local module duplicates wiring 9 modules
├── policy/terraform/            # Conftest/Rego policies — Person C
├── docs/                        # Architecture, local dev, UI gap matrix, rollback
├── .github/                     # CODEOWNERS + workflows
└── services/
    ├── _template/               # Bootstrap a new service
    ├── catalog/                 # Person A — Redis-cached product API
    ├── auth/                    # Person A — Cognito JWT verifier
    ├── cart/                    # Person B — Redis-backed cart
    ├── admin/                   # Person B — internal admin API
    ├── checkout/                # Person C — async order publisher (RDS+SQS)
    ├── invoice-worker/          # Person C — Lambda PDF/email worker
    ├── api-gateway/             # NEW — BFF for the customer-web SPA
    └── customer-web/            # NEW — vendored faybeauty React app
```

## Ownership matrix

| Area                                              | Owner   |
| ------------------------------------------------- | ------- |
| `services/{catalog,auth}` + `libs/`               | Person A |
| Network, edge, ECR Terraform                      | Person A |
| Reusable build-deploy + ci-{catalog,auth}         | Person A |
| `services/{cart,admin}` + `manifests/`            | Person B |
| EKS, Cognito, Helm add-ons Terraform              | Person B |
| `terraform-dev.yml`, ci-{cart,admin}              | Person B |
| `services/{checkout,invoice-worker}`              | Person C |
| `migrations/`, `alembic.ini`                      | Person C |
| RDS, Redis, SQS-invoice, Secrets Terraform        | Person C |
| `infra/bootstrap/`                                | Person C |
| `terraform-prod.yml` (manual approval gate)       | Person C |
| ci-{checkout,invoice-worker} + tf-* module CIs    | Person C |
| `services/{api-gateway,customer-web}`             | A+B+C    |

## Quickstart (local)

Prereqs: Docker Desktop, Node 20+, Python 3.11.

```bash
# 1. Backend stack: postgres + redis + every Python service + the gateway.
cd shopcloud
docker compose up --build

# 2. Frontend dev server (separate terminal).
cd shopcloud/services/customer-web
cp .env.example .env       # default points at http://localhost:8080
npm install
npm run dev
```

Open `http://localhost:5173` (Vite). Sign in with the seed admin
`admin@shopcloud.io` / `AdminPass1!`, or register a new shopper.

A full SPA-served-from-nginx variant (`docker compose --profile web up`) is
also available, exposed on `http://localhost:8090`.

## Local validation (pytest)

```bash
cd shopcloud
python -m pip install -e .
for svc in catalog auth cart admin checkout invoice-worker api-gateway; do
  python -m pip install -e "services/$svc[dev]"
  python -m pytest "services/$svc/tests" -q
done
```

Last full run: 148 tests pass on Python 3.11 (catalog 45, auth 40, cart 17,
admin 16, checkout 15, invoice-worker 9, api-gateway 6).

## Architecture overview

The customer-web SPA talks to the **api-gateway**, which is the
backend-for-frontend that exposes the faybeauty REST contract on top of
the AWS-native ShopCloud services. The flow:

```
React (customer-web)
   │  /api/* — JWT bearer
   ▼
api-gateway  (FastAPI)
   ├── /api/users        ──► local SQLite (dev) / Cognito (prod)
   ├── /api/products     ──► catalog (Redis-cached)
   ├── /api/cart         ──► cart (Redis)
   ├── /api/orders       ──► checkout → SQS → invoice-worker (Lambda)
   ├── /api/reviews      ──► gateway store
   ├── /api/site-reviews ──► gateway store
   └── /api/dashboard    ──► aggregated
```

See `docs/architecture.md` for a detailed walk-through and
`docs/ui-integration.md` for the gap matrix between what the React app
expects and what each ShopCloud service provides.

## Deployment

- `infra/bootstrap/` — one-time apply to create the state S3 bucket and
  DynamoDB lock table (Person C).
- `infra/envs/dev/` — apply to provision dev (Person B owns the pipeline).
- `infra/envs/prod/` — apply to provision prod (Person C owns the pipeline,
  manual approval gate via GitHub Environments).
- `manifests/` — `kubectl apply -k manifests/` after CI replaces the
  `PLACEHOLDER_*` tokens. The runbook for replacements lives in
  `docs/local-dev.md`.

## Rollback

If a release misbehaves:

```bash
# 1. Roll the deployment back to the previous ReplicaSet.
kubectl -n app rollout undo deployment/<service>

# 2. Or pin a known-good image SHA via workflow_dispatch.
gh workflow run reusable-build-deploy.yml -f service=<svc> -f image_tag=<sha>

# 3. DB migrations: never destructive in the same release that ships
#    new code. See docs/rollback.md (two-phase migration policy).
```

Full runbook: `docs/rollback.md`.
