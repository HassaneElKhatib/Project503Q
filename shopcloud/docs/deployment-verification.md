# Deployment verification (architecture vs runtime)

This checklist maps your **Project Architecture** document to checks you can run before a deadline. Full AWS parity (multi-region latency bonus, Shield Advanced, strict WAF rules) is optional beyond core correctness.

**Timeboxed deadline (~5 hours):** aim for P0 items first—correct overlay per cluster, ExternalSecrets synced, storefront + login + checkout smoke. Full VPN admin path, invoice Lambda→S3→SES, and CloudFront/WAF parity often need longer windows (DNS propagation, SES sandbox, VPN provisioning).

## Separation quick check

| Item | Prod overlay | Dev overlay |
|------|----------------|-------------|
| Build command | `kubectl kustomize shopcloud/manifests/overlays/prod` | `kubectl kustomize shopcloud/manifests/overlays/dev` |
| Apply command | `kubectl apply -k shopcloud/manifests/overlays/prod` | `kubectl apply -k shopcloud/manifests/overlays/dev` |
| Namespace | `app` | `app-dev` |
| Secrets Manager paths | `/shopcloud/prod/...` | `/shopcloud/dev/...` |
| ECR image prefix | `shopcloud-prod-*` | `shopcloud-dev-*` |
| Public ALB group | `shopcloud-public` | `shopcloud-public-dev` |
| Admin ALB group | `shopcloud-admin` | `shopcloud-admin-dev` |
| VPC CIDR in NetworkPolicy (ALB → pods) | `10.30.0.0/16` | patched to `10.20.0.0/16` |

Ensure Terraform has created **dev** secrets under `/shopcloud/dev/*` before applying the dev overlay.

## Customer path (public)

Architecture: Route 53 → CloudFront → WAF → **internet-facing ALB** → EKS (LB Controller).

**Checks**

1. DNS resolves to CloudFront (if enabled) or ALB hostname from ingress status.
2. HTTPS works where ACM is attached (prod ingress uses HTTPS; dev overlay defaults to **HTTP 80** until you add ACM + HTTPS annotations).
3. From browser: load storefront `/`, assets load, no mixed-content errors vs `public_origin` in ConfigMap.
4. `/auth/*` reaches auth service; `/api/*` reaches api-gateway.

**Commands (adjust context and namespace)**

```bash
kubectl get ingress -n app
kubectl get ingress -n app-dev
```

## Admin path (private)

Architecture: **Client VPN** → **internal ALB** → separate ingress → admin/auth routes.

**Checks**

1. Connect VPN using your dev/prod Client VPN endpoint (certificate + MFA per design).
2. Resolve internal admin hostname (private Route53 zone or `/etc/hosts` toward internal ALB).
3. `curl -v https://<admin-host>/health/live` (or HTTP if using dev overlay listener).
4. Admin UI/API routes `/api/admin` hit admin service; `/api/me` hits auth.

Update **`alb.ingress.kubernetes.io/inbound-cidrs`** on admin ingress if VPN allocates subnets outside `10.20`/`10.30`.

## EKS workload layer (five core services + edge)

Architecture lists catalog, cart, checkout, auth, admin; this repo also ships **api-gateway** and **customer-web**.

**Checks**

```bash
NS=app   # or app-dev
kubectl get deploy,po -n $NS
kubectl get hpa -n $NS
```

Expect **≥ 2 ready replicas** per deployment where HPA allows it.

## Identity & secrets

Architecture: **Cognito** (customer + admin pools), **Secrets Manager** via IRSA / External Secrets.

**Checks**

1. ExternalSecrets **Synced** and Kubernetes Secrets exist (`shared-database`, `shared-redis`, cognito secrets, `invoice-queue`, `api-gateway-jwt`).
2. Customer login (hosted UI or app OAuth): tokens validate at gateway.
3. Admin login uses **admin** pool credentials only.

```bash
kubectl get externalsecret -n $NS
kubectl describe externalsecret shared-database -n $NS
```

## Data layer

Architecture: **RDS PostgreSQL**, **ElastiCache Redis**.

**Checks**

1. Catalog/browse reads succeed (DB).
2. Cart persistence survives refresh (Redis).
3. Run migrations Job once per deploy (`shopcloud/manifests/migrations/job.yaml` via overlay).

## Invoice pipeline (async)

Architecture: checkout → **SQS** → **Lambda** → **S3** PDF → **SES** email.

**Checks**

1. Complete a checkout that should enqueue an invoice.
2. SQS queue depth decreases; Lambda succeed count increases (CloudWatch).
3. Object appears in invoices bucket; SES sends (sandbox limits apply).

## Timeboxed deadline (~5h) recommendation

| Priority | Task |
|----------|------|
| P0 | Apply correct overlay per cluster; confirm namespaces + ExternalSecrets paths |
| P0 | Smoke: storefront loads, login, add-to-cart, checkout happy path |
| P1 | Admin path over VPN + internal ALB |
| P1 | One invoice end-to-end (SQS → Lambda → S3 → SES) |
| P2 | CloudFront + WAF + Shield parity audit vs PDF wording |

If anything fails, capture **`kubectl describe`** on failing Ingress / ExternalSecret / Pod and the first failing dependency (DNS, ACM, OIDC, Secrets path).
