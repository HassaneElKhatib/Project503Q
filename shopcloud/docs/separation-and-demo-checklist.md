# ShopCloud: separation + architecture verification (master checklist)

Work top to bottom. Check boxes as you complete items.

## Phase A — Repo & safety baseline

- [ ] **A1. Persist manifests and infra in Git** — commit `manifests/overlays/`, dev `backend.tf`, docs; never commit Secrets Manager values or kubeconfig.
- [ ] **A2. Branch strategy** — use `main`/`dev` (or your agreed integration branch); avoid deploying prod from feature branches by mistake.
- [ ] **A3. Kube context discipline** — document `kubectl config use-context` for dev vs prod; add shell aliases if helpful.

## Phase B — Terraform parity (codify manual drift)

Manual fixes during bring-up should match Terraform on next apply:

- [ ] **B1. Dev VPC subnets** — ALB controller tags: `kubernetes.io/role/elb`, `kubernetes.io/role/internal-elb`, `kubernetes.io/cluster/<cluster-name>=shared` on correct subnets.
- [ ] **B2. Security groups** — RDS SG allows `5432` from EKS node SG; Redis SG allows `6379` from EKS node SG.
- [ ] **B3. EKS access** — authentication mode `API_AND_CONFIG_MAP` (or your chosen mode); access entries / `aws-auth` for operators and CI roles.
- [ ] **B4. External Secrets IRSA** — role `shopcloud-dev-eks-external-secrets` can `secretsmanager:GetSecretValue` on `/shopcloud/dev/*` (and prod equivalent).
- [ ] **B5. Secrets existence** — `/shopcloud/dev/api-gateway/jwt` (JSON `secret`) and all Cognito paths created by Terraform or documented runbooks.

## Phase C — Kubernetes deploy (repeatable)

- [ ] **C1. Dev deploy** — `kubectl apply -k shopcloud/manifests/overlays/dev` on **dev** context.
- [ ] **C2. Prod deploy** — `kubectl apply -k shopcloud/manifests/overlays/prod` on **prod** context (when changing prod manifests).
- [ ] **C3. Migrations** — ensure `db-migrate` Job completes after RDS reachable (`kubectl logs job/db-migrate -n <ns>`).
- [ ] **C4. Legacy manifest dirs** — stop editing `shopcloud/manifests/catalog/` etc.; treat `overlays/prod/base/` as canonical (see `manifests/README.md`).

## Phase D — Architecture PDF verification

### Customer path (public)

- [ ] **D1. DNS** — public hostname points to CloudFront or ALB per design.
- [ ] **D2. TLS** — HTTPS where required (prod certainly; dev optional but document).
- [ ] **D3. WAF / Shield** — prod edge controls present or explicitly scoped as phase 2.
- [ ] **D4. Browser smoke** — storefront, navigation, assets load; mixed-content none.

### Identity

- [ ] **D5. Cognito (customer + admin pools)** — callback/logout URLs match **environment** hostnames; cookie domain isolated dev vs prod.

### EKS workloads

- [ ] **D6. Microservices + gateway + frontend** — all Deployments ready; HPA/PDB as designed.
- [ ] **D7. Internal service mesh** — cluster DNS names (`http://catalog`, etc.) resolve between pods.

### Data

- [ ] **D8. RDS PostgreSQL** — catalog/checkout/admin paths hit DB; backups/Multi-AZ per env design.
- [ ] **D9. Redis** — cart/session paths work; TLS/auth settings match secret URLs.

### Async invoicing

- [ ] **D10. Checkout → SQS** — enqueue on successful checkout.
- [ ] **D11. Lambda worker** — processes message; logs/metrics clean.
- [ ] **D12. S3 invoice object** — object lands in correct bucket/prefix.
- [ ] **D13. SES** — email sends (verify identities / sandbox constraints).

### Admin path (private)

- [ ] **D14. Client VPN** — staff connect with cert/MFA per design.
- [ ] **D15. Internal ALB + DNS** — admin host resolves only inside VPC/VPN; `/api/admin` and `/api/me` routes work.

### Bonus (multi-region latency)

- [ ] **D16.** Route 53 latency routing / secondary region — only if in scope.

## Phase E — CI/CD hardening

- [ ] **E1. Separate OIDC roles** — dev workflows cannot assume prod roles.
- [ ] **E2. Branch filters** — image push and Terraform apply gated by branch + GitHub Environment approvals for prod.
- [ ] **E3. Immutable tags** — promote SHA/digest from dev validation to prod release.

---

Reference: build commands and architecture-aligned smoke ideas live in `shopcloud/docs/deployment-verification.md`.
