# ShopCloud Architecture

A FastAPI microservice e-commerce platform deployed on EKS, fronted by a
React/Vite SPA, backed by RDS Postgres + ElastiCache Redis + an SQS-driven
Lambda invoice worker, with traffic shaped by CloudFront + WAF and the AWS
Load Balancer Controller.

## Service map

| Service          | Lang     | Owner | Synchronous deps          | Async/storage         |
| ---------------- | -------- | ----- | ------------------------- | --------------------- |
| `customer-web`   | React 19 | A+B+C | api-gateway               | —                     |
| `api-gateway`    | FastAPI  | A+B+C | catalog, cart, checkout, admin, auth | gateway DB |
| `catalog`        | FastAPI  | A     | RDS reader, Redis (cache) | —                     |
| `auth`           | FastAPI  | A     | Cognito                   | signed state cookies  |
| `cart`           | FastAPI  | B     | Redis, catalog (price)    | —                     |
| `admin`          | FastAPI  | B     | RDS reader, Cognito admin | —                     |
| `checkout`       | FastAPI  | C     | RDS writer, Redis         | SQS-invoice           |
| `invoice-worker` | Lambda   | C     | RDS reader                | S3 invoices, SES      |

## Customer journey

1. Browser loads SPA assets from CloudFront.
2. SPA calls `GET /api/products` → CloudFront → public ALB → api-gateway →
   catalog (Redis-cached read of the read replica).
3. Sign-in: SPA `POST /api/users/login` → api-gateway issues a JWT (local
   mode) or redirects to Cognito Hosted UI (prod auth path via the auth
   service); the resulting JWT is stored client-side and forwarded.
4. Add to cart: SPA `POST /api/cart/add` → api-gateway → cart service
   (Redis hash keyed by user id).
5. Checkout: SPA `POST /api/orders` → api-gateway → checkout service →
   inserts the order in RDS (write endpoint) → publishes `OrderCreated`
   to SQS → returns 202 immediately. Customer never blocks on email.
6. invoice-worker Lambda consumes SQS → renders PDF → uploads to S3 →
   `SendRawEmail` via SES.

## Why a BFF (api-gateway)

The vendored React UI was built against a MERN-style API (single
backend, JSON login/register, MongoDB-shaped IDs). ShopCloud's services
are AWS-native (Cognito redirect-based auth, JWT validation per service,
RDS for orders, Redis for cart). The api-gateway:

- Maps the SPA's REST contract to the underlying services where they
  exist (catalog/cart/checkout/admin).
- Implements features the SPA needs but that ShopCloud doesn't ship
  (reviews, site-reviews, dashboard analytics).
- Handles bearer-token auth in dev and forwards to the auth service in
  prod (configurable via `AUTH_BASE_URL`).
- Decouples UI velocity from microservice contract changes.

## Networking

- VPC with 6 subnets across 2 AZs: 2 public (NAT + ALB), 2 private app
  (EKS), 2 private data (RDS, Redis).
- 1 NAT gateway in dev, 2 in prod for AZ-resilience.
- VPC endpoints for ECR API, ECR DKR, S3, Secrets Manager, KMS, STS to
  keep traffic off the public internet.
- VPC flow logs to CloudWatch with 14-day retention.

## Edge

- Route 53 hosted zone per env (dev, prod).
- ACM cert in `us-east-1` for CloudFront, ACM cert in primary region for
  the public ALB. Both DNS-validated.
- CloudFront with WAFv2 managed rule groups (Common, KnownBadInputs,
  AmazonIpReputation) attached at the distribution level.
- Latency-based Route 53 records for EU origin in front of the regional
  ALB.

## Cluster (EKS)

- EKS 1.29 with envelope encryption for Kubernetes Secrets via a
  customer-managed KMS key.
- Managed node group across 2 AZs.
- IRSA (one role per microservice — least privilege).
- Helm releases (via `eks_helm_addons` module): AWS Load Balancer
  Controller, External Secrets Operator, metrics-server, Cluster
  Autoscaler.
- ExternalSecrets sync RDS / Redis / SQS-invoice / Cognito secrets from
  Secrets Manager into Kubernetes Secrets per service.

## Data plane

- **RDS**: Postgres Multi-AZ in primary region, KMS-encrypted; in prod a
  cross-region read replica in `eu-west-1`. Catalog reads from the
  reader endpoint; checkout writes to the writer.
- **Redis**: ElastiCache replication group with encryption in transit
  and at rest, used by cart (sessions) and catalog (cache-aside).
- **SQS-invoice**: standard queue with a DLQ, fed by checkout and
  consumed by the invoice-worker Lambda; DLQ messages alarm on
  `ApproximateNumberOfMessagesVisible > 0`.
- **S3 invoices bucket**: versioned, blocked from public access,
  SSE-KMS, lifecycle rule expiring incomplete multiparts.
- **SES**: verified `from` identity, sandboxed off in prod.
- **Secrets**: Secrets Manager + External Secrets Operator
  ClusterSecretStore wiring; the `secrets` Terraform module produces an
  index secret listing the shared ARNs so each service's
  `ExternalSecret` can reference one well-known ARN.

## Observability

- structured JSON logs via `libs/logger`.
- Prometheus metrics exposed on each service via `libs/health`.
- Read replica drift, cart Redis CPU, SQS DLQ depth, Lambda errors are
  the standard alarms.

## Disaster recovery

- RDS automated backups: 1 day in dev, 7 days in prod.
- RDS prod has a cross-region read replica for failover.
- S3 invoices bucket is versioned and replicated when prod replication
  is needed.
- Terraform state in S3 with versioning + DynamoDB locks (bootstrap
  module).
