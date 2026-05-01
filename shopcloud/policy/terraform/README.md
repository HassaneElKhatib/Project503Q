# Terraform Policies (OPA / Conftest)

These Rego policies are evaluated against `terraform plan` JSON output by the
`terraform-prod` workflow.

## Policies

- `security.rego` — security guardrails (encryption, no public access, KMS, etc.)
- `tags.rego` — required tags (warn-only): `Project`, `Environment`, `ManagedBy`

## Run locally

```bash
cd infra/envs/prod
terraform init
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
conftest test tfplan.json --policy ../../../policy/terraform --all-namespaces
```

## Add a new policy

1. Create `<topic>.rego` in this directory under package `terraform.<topic>`.
2. Use `deny contains msg if { ... }` to fail the pipeline.
3. Use `warn contains msg if { ... }` to surface a soft warning.
4. The CI pipeline picks it up automatically.
