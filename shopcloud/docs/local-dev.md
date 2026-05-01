# Local development

This guide takes a fresh checkout to a working full-stack dev environment.

## Prerequisites

- Python 3.11 (Anaconda or system) — `python -V` should print 3.11.x
- Docker Desktop (or any OCI runtime + compose v2)
- Node 20+ and `npm`
- Optional: Terraform 1.7+, AWS CLI v2

## 1. Backend services

```bash
cd shopcloud
docker compose up --build
```

This brings up:

| Container     | Host port | What it does                              |
| ------------- | --------- | ----------------------------------------- |
| postgres      | 5432      | RDS stand-in for checkout/admin           |
| redis         | 6379      | ElastiCache stand-in for cart/catalog     |
| catalog       | 8001      | Read-only product API                     |
| auth          | 8002      | Cognito JWT verifier (mocked in dev)      |
| cart          | 8003      | Redis-backed cart                         |
| checkout      | 8004      | Async order publisher                     |
| admin         | 8005      | Admin orders/users API                    |
| api-gateway   | 8080      | BFF the SPA talks to                      |

### Run individual services without docker

```bash
python -m pip install -e .
python -m pip install -e "services/catalog[dev]"
PRODUCTS_JSON_PATH=services/catalog/data/products.json \
  python -m uvicorn app.main:app --reload --app-dir services/catalog --port 8001
```

(Replace `catalog` with whichever service you're running.)

## 2. Frontend

```bash
cd shopcloud/services/customer-web
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`.

The SPA reads its backend URL from `VITE_BACKEND_URL` (defaults to
`http://localhost:8080`, which is the api-gateway).

## 3. Seed admin

The api-gateway seeds an admin on first run:

| Field    | Value                  |
| -------- | ---------------------- |
| Email    | `admin@shopcloud.io`   |
| Password | `AdminPass1!`          |

Override with `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` in
`services/api-gateway/.env`.

## 4. Running the test suites

Every service has a self-contained test suite.

```bash
cd shopcloud
python -m pip install -e .
for svc in catalog auth cart admin checkout invoice-worker api-gateway; do
  python -m pip install -e "services/$svc[dev]"
  python -m pytest "services/$svc/tests" -q
done
```

148 tests should pass on Python 3.11.

## 5. Terraform (optional)

```bash
cd infra/bootstrap
terraform init
terraform apply             # creates the state bucket + lock table

cd ../envs/dev
cp backend.hcl.example backend.hcl
cp terraform.tfvars.example terraform.tfvars
# Edit both: replace REPLACE_* placeholders.
terraform init -backend-config=backend.hcl
terraform plan
```

Each env-root duplicates the modules under `./modules/`, so you can
validate dev independently of prod. CI runs `fmt -check`, `validate`,
`tflint`, `tfsec`, `plan` on PR via the `terraform-dev`/`terraform-prod`
workflows.

## 6. Database migrations

```bash
cd shopcloud
DATABASE_URL=postgresql+asyncpg://shopcloud:shopcloud@localhost:5432/shopcloud \
  alembic upgrade head
```

To create a new migration:

```bash
DATABASE_URL=postgresql+asyncpg://shopcloud:shopcloud@localhost:5432/shopcloud \
  alembic revision --autogenerate -m "describe the change"
```

Migrations are applied in-cluster via `manifests/migrations/job.yaml`
during a release; see `docs/rollback.md` for the two-phase migration
policy.

## 7. Common issues

**`ModuleNotFoundError: app`**: another service is using the same
`app` package name. Run tests one service at a time, or invoke
`pytest services/<svc>/tests` from the repo root with that service's
package installed.

**`unable to open database file`** in api-gateway tests: delete
`%TEMP%\shopcloud-gateway-tests.db` and re-run. The conftest already
does this on startup.

**Port 8080 in use**: another service is bound. Either stop it or set
`API_GATEWAY_PORT` and re-export `VITE_BACKEND_URL` in
`services/customer-web/.env`.
