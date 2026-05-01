# Teammate Handoff

This is a heads-up to B and C: most of the app code is already done and
tested. Your DevOps work (Terraform + CI/CD) is unblocked. The notes
below tell you exactly where to plug in.

## What's already done (don't redo)

- All 5 microservices are written and tested (142 tests passing)
- The Lambda invoice worker is written and tested
- All Kubernetes manifests are written
- Alembic migrations are written (run before any service starts)
- Shared libs (logging, JWT verification, error handling, DB session, SQS publisher) are all in `libs/`


---

## Person B — your work

You own:

1. **`services/cart/`** — code is done. Read it; you'll be asked about it in the demo.
2. **`services/admin/`** — code is done. Read it.
3. **Terraform module: `infra/modules/eks`**
4. **Terraform module: `infra/modules/cognito`**
5. **GitHub Actions: `.github/workflows/terraform-dev.yml`**

### infra/modules/eks must expose

This module creates the EKS cluster, node groups, and installs add-ons.

**Resources:**
- `aws_eks_cluster` with the cluster
- `aws_eks_node_group` (managed) — at least 2 instances, spread across 3 AZs
- `aws_iam_openid_connect_provider` — for IRSA
- IAM role per service: `catalog-irsa`, `auth-irsa`, `cart-irsa`, `admin-irsa`, `checkout-irsa`, `db-migrate-irsa`
  - **catalog-irsa**: `secretsmanager:GetSecretValue` on shared-database, shared-redis only
  - **auth-irsa**: `secretsmanager:GetSecretValue` on cognito-customer only
  - **cart-irsa**: `secretsmanager:GetSecretValue` on shared-redis, cognito-customer
  - **admin-irsa**: `secretsmanager:GetSecretValue` on shared-database, cognito-admin; `cognito-idp:ListUsers` (if you need it)
  - **checkout-irsa**: `secretsmanager:GetSecretValue` on shared-database, shared-redis, cognito-customer, invoice-queue; **`sqs:SendMessage` on the invoice queue ARN ONLY** (this is the key one — checkout must NOT have wildcard SQS access)
  - **db-migrate-irsa**: `secretsmanager:GetSecretValue` on shared-database
- `helm_release` for: AWS Load Balancer Controller, External Secrets Operator, metrics-server, Cluster Autoscaler

**Outputs:**
- `cluster_name` (string) — used by CI to do `aws eks update-kubeconfig`
- `cluster_endpoint` (string)
- `cluster_certificate_authority_data` (string, base64)
- `oidc_provider_arn` (string)
- For each service: `<service>_irsa_role_arn` — these go into the ServiceAccount manifests' `eks.amazonaws.com/role-arn` annotation

### infra/modules/cognito must expose

Two user pools: customer and admin.

**Resources:**
- `aws_cognito_user_pool` (customer) with hosted-UI domain, password policy, optional MFA
- `aws_cognito_user_pool_client` (customer) with allowed callback URLs (`https://<host>/auth/callback`), allowed logout URLs, OAuth flows = code + scopes openid+email+profile
- `aws_cognito_user_pool_domain` (customer)
- Same trio for admin
- `aws_cognito_user_group` "admin" inside the admin pool
- Two `aws_secretsmanager_secret` entries:
  - `/shopcloud/<env>/cognito/customer` — JSON: `user_pool_id`, `app_client_id`, `region`, `domain`, `callback_url`, `logout_redirect_url`, `cookie_domain`, `state_signing_key` (random)
  - `/shopcloud/<env>/cognito/admin` — JSON: `user_pool_id`, `app_client_id`, `region`

**Outputs:**
- `customer_user_pool_id`, `admin_user_pool_id`
- `customer_app_client_id`, `admin_app_client_id`

### .github/workflows/terraform-dev.yml needs to

1. Trigger on push to `dev` branch when `infra/envs/dev/**` or `infra/modules/**` changes
2. Use OIDC federation to assume `github-actions-dev` IAM role (Person A sets up the trust)
3. Run `terraform fmt -check`, `terraform validate`, `tflint`, `tfsec`
4. On PR: `terraform plan` and post the plan as a PR comment
5. On merge: `terraform apply -auto-approve`
6. **No prod credentials in this workflow.** This is dev-only.

### GitHub → AWS OIDC for Terraform Dev (fix `AssumeRoleWithWebIdentity`)

CI assumes IAM role `shopcloud-dev-github-actions-dev` (see `.github/workflows/terraform-dev.yml`).
If the job fails with **`Not authorized to perform sts:AssumeRoleWithWebIdentity`**, the role **trust policy**
does not match GitHub’s OIDC **`sub`** claim.

**Important:** `pull_request` events use a subject like `repo:<owner>/<repo>:pull_request`.
Push events use `repo:<owner>/<repo>:ref:refs/heads/<branch>`.
If the trust policy only lists `ref:refs/heads/...`, **PR plans fail** while pushes might still work.

1. IAM → **Identity providers** — ensure `token.actions.githubusercontent.com` exists (create via AWS docs if missing).
2. IAM → role **`shopcloud-dev-github-actions-dev`** → **Trust relationships** — include PR + branches your workflows use.

Example trust policy (replace `<ACCOUNT_ID>`; adjust `repo:` if the GitHub repo name differs):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:HassaneElKhatib/Project503Q:pull_request",
            "repo:HassaneElKhatib/Project503Q:ref:refs/heads/dev",
            "repo:HassaneElKhatib/Project503Q:ref:refs/heads/main"
          ]
        }
      }
    }
  ]
}
```

Compare with the working **`shopcloud-prod-github-actions-prod`** trust policy and align dev’s **`sub`** patterns.

**Fork PRs:** GitHub does not grant OIDC tokens to workflows triggered from forks unless you opt into insecure patterns — prefer PR branches on the same repo for Terraform plans.

Dev Terraform state backend for CI is defined in `infra/envs/dev/backend.tf` (same idea as prod’s `backend.tf`). Local `-backend-config=backend.hcl` overrides are optional if your buckets differ.

### Critical detail you'll trip on

The AWS Load Balancer Controller helm chart needs annotations on its
ServiceAccount with the IRSA role ARN. There's a chicken-and-egg: you
need the OIDC provider ARN to make the role, but the OIDC provider needs
the EKS cluster. Pattern:

```hcl
data "tls_certificate" "eks" { url = aws_eks_cluster.this.identity[0].oidc[0].issuer }
resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.this.identity[0].oidc[0].issuer
}
```

Then build IRSA roles using that OIDC ARN. Stage the apply if needed.

---

## Person C — your work

You own:

1. **`services/checkout/`** — code is done. Read it.
2. **`services/invoice-worker/`** — code is done. Read it.
3. **`migrations/`** — Alembic migrations are written. You'll trigger them in the deploy pipeline.
4. **Terraform module: `infra/modules/rds`**
5. **Terraform module: `infra/modules/redis`**
6. **Terraform module: `infra/modules/sqs-invoice`**
7. **Terraform module: `infra/modules/secrets`** (Secrets Manager entries)
8. **GitHub Actions: `.github/workflows/terraform-prod.yml`** (with manual approval gate)

### infra/modules/rds must expose

**Resources:**
- `aws_db_subnet_group` in private data subnets
- `aws_db_instance`:
  - dev: `db.t3.medium`, 50GB storage, single-AZ
  - prod: `db.r6g.large`, 200GB, **`multi_az = true`**, `storage_encrypted = true` with KMS CMK, `deletion_protection = true`
  - `parameter_group` setting `rds.force_ssl = 1`
- For prod: `aws_db_instance` (replica) in eu-west-1 — `replicate_source_db = aws_db_instance.primary.arn`
- `aws_db_parameter_group` if you tune anything
- Master password from `random_password` -> stored in Secrets Manager, never in tfvars
- Two Secrets Manager entries with the URL strings (since services need URLs not raw fields):
  - `writer_url` = `postgresql://shopcloud:${pw}@${primary_endpoint}/shopcloud`
  - `reader_url` = `postgresql://shopcloud:${pw}@${reader_endpoint}/shopcloud` (in same region; cross-region replica would need a separate URL)

**Outputs:**
- `writer_endpoint`, `reader_endpoint`
- `secret_arn_database`

### infra/modules/redis must expose

**Resources:**
- `aws_elasticache_subnet_group` in private data subnets
- `aws_elasticache_replication_group`:
  - dev: 1 node, no automatic failover
  - prod: `multi_az_enabled = true`, `automatic_failover_enabled = true`, `at_rest_encryption_enabled = true`, `transit_encryption_enabled = true`, AUTH token from Secrets Manager
- Secrets Manager entry with the URL (`rediss://:${auth_token}@${primary_endpoint}:6379`)

**Outputs:**
- `primary_endpoint`
- `secret_arn_redis`

### infra/modules/sqs-invoice must expose

**Resources:**
- `aws_sqs_queue` (main) with 4-hour visibility timeout, `redrive_policy` to DLQ after 5 receives
- `aws_sqs_queue` (dlq)
- `aws_lambda_function` `shopcloud-invoice-worker-${env}`:
  - runtime: `python3.12`
  - handler: `handler.lambda_handler`
  - filename = path to `services/invoice-worker/dist/invoice-worker.zip` (built by `services/invoice-worker/build.sh`)
  - env vars: `INVOICES_BUCKET`, `SES_FROM_ADDRESS`, `KMS_KEY_ARN`
  - reserved_concurrent_executions: 5 (caps the parallelism)
  - **`event_source_mapping`** with the SQS queue, batch size 10, **`function_response_types = ["ReportBatchItemFailures"]`** (this is what makes partial-batch failure work)
- `aws_s3_bucket` `shopcloud-invoices-${env}` with SSE-KMS, BlockPublicAccess on, lifecycle to Glacier after 90 days
- `aws_ses_email_identity` for the From address (verify with SES)
- IAM execution role for the Lambda: `sqs:Receive*/Delete*` on the queue ARN, `s3:PutObject` on the bucket prefix `invoices/*`, `ses:SendRawEmail`, `kms:Encrypt/Decrypt` on the CMK
- Secrets Manager entry `/shopcloud/<env>/sqs/invoice` with the queue URL

**Outputs:**
- `invoice_queue_url`
- `invoice_queue_arn` (checkout's IRSA needs this for tight `sqs:SendMessage`)
- `invoices_bucket_name`

### .github/workflows/terraform-prod.yml needs to

Same shape as Person B's dev pipeline but:
- Triggers on push to `main`
- Uses prod OIDC role
- **Has a `environment: prod` on the apply job** — GitHub Environments protection rule requires reviewers to approve before apply runs
- Plan is posted on PR; apply waits for approval after merge

---

## Person A — what's left for you

(For reference, since A is coordinating.)

1. **Terraform: bootstrap, network, edge, ECR**
   - `infra/bootstrap/` — S3 state buckets + DynamoDB lock tables (one set per env)
   - `infra/modules/network` — VPC, 9 subnets across 3 AZs, NAT, IGW, VPC endpoints, Flow Logs
   - `infra/modules/edge` — Route 53 zone, ACM cert (DNS-validated), CloudFront distribution, WAF WebACL with managed rule groups
   - `infra/modules/ecr` — 6 repositories with immutable tags + lifecycle policy
   - `infra/modules/vpn` — Client VPN endpoint with cert + SAML federation for MFA

2. **GitHub Actions: reusable workflow + per-service workflows**
   - `.github/workflows/reusable-build-deploy.yml` — the test/build/scan/push/deploy template
   - 6× `.github/workflows/ci-<service>.yml` — one for each service (catalog, auth, cart, admin, checkout, invoice-worker)
   - Branch protection on `main` and `dev`
   - GitHub Environments setup with prod approvers
   - OIDC trust setup in AWS (root once, then per-env IAM roles)

3. **Architecture diagram** (whiteboard photo or draw.io)

4. **Cost estimate** (already in README, refine after Terraform shows real values)

5. **Demo script** — who clicks what, in what order

---

## Pair points (where two people block each other)

- **A+B**: public ALB <-> Ingress controller annotations. A's ACM cert ARN goes into B's manifests; B's LB controller has to be installed before A's ingress works.
- **A+B**: Cognito user pool IDs from B's module flow into A's Secrets Manager entries (or B owns those secret entries — agree before writing).
- **B+C**: External Secrets Operator (B installs) pulling Secrets Manager entries (C creates) into K8s Secrets.
- **B+C**: checkout's IRSA role (B owns) needs the SQS queue ARN (C's output). Wire `module.sqs_invoice.invoice_queue_arn` → `module.eks.checkout_irsa_policy_resource`.
- **A+C**: CloudFront origin pointing at A's public ALB DNS.

## Daily 15-min standup format

Each person, 3 minutes:
1. What I shipped yesterday (link the PR or commit)
2. What I'm shipping today
3. What's blocking me / who I need

Resolve blockers immediately or escalate to morning swarm.
