# Rollback runbook

## Decision tree

```
Bad release? ──► is the deployment crashing?
                      │
                      ├── yes ──► kubectl rollout undo (Step 1)
                      │
                      └── no ──► is data corrupt?
                                      │
                                      ├── yes ──► follow Step 3 (DB rollback)
                                      │
                                      └── no ──► pin to last green SHA (Step 2)
```

## Step 1 — `kubectl rollout undo`

Fastest path. Reverts the Deployment to the previous ReplicaSet without
needing a CI run.

```bash
kubectl -n app rollout undo deployment/<service>
kubectl -n app rollout status deployment/<service>
```

If the previous ReplicaSet was also broken, scale the deployment to 0,
ship the fix, then scale back up:

```bash
kubectl -n app scale deployment/<service> --replicas=0
# fix forward, then:
kubectl -n app scale deployment/<service> --replicas=2
```

## Step 2 — Pin to a known-good image SHA

If the rollback ReplicaSet is gone (max history reached) or you need a
specific previous build, redeploy with `workflow_dispatch`:

```bash
gh workflow run reusable-build-deploy.yml \
  -f service=<service> \
  -f image_tag=<12-char-sha>
```

The `reusable-build-deploy.yml` template tags images with the commit
SHA, so any historical green build is recoverable from ECR.

## Step 3 — Database rollback

**The golden rule: never ship a destructive migration in the same
release as code that depends on it.**

Two-phase migration policy:

1. **Phase 1 release** — additive migration only.
   - Add new columns/tables. Default to NULL or a sentinel value.
   - Do NOT remove columns. Do NOT rename. Do NOT drop tables.
   - Ship app code that *can* read both old and new shapes (feature
     flagged off).
2. **Phase 2 release** — turn the feature flag on. Backfill the new
   columns asynchronously (via a one-off Job that runs the
   `manifests/migrations/job.yaml` pattern with a backfill script).
3. **Phase 3 release** — once Phase 2 has been live for at least one
   release cycle, ship the destructive migration to remove old columns.

This means you can always roll back the *code* without rolling back the
*schema*. If you genuinely must roll back a migration:

```bash
# Find the previous revision id.
alembic history --verbose | head -20

# Downgrade ONE step.
DATABASE_URL=postgresql+asyncpg://... alembic downgrade -1
```

Never `alembic downgrade` against prod without first taking a snapshot:

```bash
aws rds create-db-snapshot \
  --db-instance-identifier shopcloud-prod-postgres \
  --db-snapshot-identifier prerollback-$(date +%Y%m%d-%H%M)
```

## Step 4 — Async pipeline rollback (invoice-worker)

Bad messages go to the DLQ:

```bash
# Inspect DLQ depth
aws sqs get-queue-attributes \
  --queue-url $INVOICE_QUEUE_DLQ_URL \
  --attribute-names ApproximateNumberOfMessages

# Replay good messages from DLQ to main queue (after fixing the bug)
aws sqs receive-message --queue-url $INVOICE_QUEUE_DLQ_URL \
  --max-number-of-messages 10 \
  --visibility-timeout 60 | jq -c '.Messages[]' | while read m; do
    body=$(echo "$m" | jq -r .Body)
    handle=$(echo "$m" | jq -r .ReceiptHandle)
    aws sqs send-message --queue-url $INVOICE_QUEUE_URL --message-body "$body"
    aws sqs delete-message --queue-url $INVOICE_QUEUE_DLQ_URL --receipt-handle "$handle"
  done
```

Lambda function rollback uses versioning + aliases:

```bash
aws lambda update-alias \
  --function-name shopcloud-invoice-worker \
  --name live \
  --function-version <previous-version>
```

## Step 5 — Edge / DNS rollback

CloudFront invalidations are minutes-not-seconds; if a bad SPA build is
live, also bump the `index.html` cache key by deploying a previous SPA
version (steps 1+2 above for the `customer-web` deployment).

DNS changes (Route 53 record updates) typically propagate within minutes
because TTLs are 60s by default for app records.

## Communications

- Update the incident channel.
- Post the rollback action + the commit SHA you rolled back to.
- Open a follow-up issue with the root cause.
- Update `docs/architecture.md` if any invariant changed during the fix.
