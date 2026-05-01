# Kubernetes manifests (ShopCloud)

## Deploy

```bash
kubectl apply -k shopcloud/manifests/overlays/prod   # namespace app
kubectl apply -k shopcloud/manifests/overlays/dev    # namespace app-dev
```

Root [`kustomization.yaml`](kustomization.yaml) delegates to **`overlays/prod`** for backward compatibility.

## Layout

| Path | Role |
|------|------|
| [`overlays/prod/base/`](overlays/prod/base/) | **Canonical** workloads + prod cluster resources (ingress, ExternalSecrets, prod DB paths, prod IRSA ARNs). |
| [`overlays/prod/kustomization.yaml`](overlays/prod/kustomization.yaml) | Prod overlay (`namespace: app`). |
| [`overlays/dev/kustomization.yaml`](overlays/dev/kustomization.yaml) | Dev overlay: dev namespace, `/shopcloud/dev/*` secrets, dev VPC NetworkPolicy patch, dev ECR images, dev ingress defaults. |
| [`overlays/dev/base/`](overlays/dev/base/) | Copy of workloads + shared cluster pieces; **sync from prod/base** when you change deployments (then re-apply IRSA + dev-specific cluster files as needed). |

Top-level folders [`cluster/`](cluster/), [`catalog/`](catalog/), etc. are **legacy duplicates** of `overlays/prod/base/` unless you remove them—prefer editing **`overlays/prod/base/`** to avoid drift.

## Dev overlay sync (after editing prod/base)

Do **not** wholesale mirror prod→dev: keep [`overlays/dev/base/kustomization.yaml`](overlays/dev/base/kustomization.yaml) and dev-only cluster omissions.

Typical flow: copy changed workload dirs (`catalog/`, `auth/`, …) from `overlays/prod/base/` into `overlays/dev/base/`, then replace IRSA ARNs:

```powershell
Get-ChildItem shopcloud\manifests\overlays\dev\base -Recurse -Filter *.yaml | ForEach-Object {
  (Get-Content $_.FullName -Raw) -replace 'shopcloud-prod-eks-','shopcloud-dev-eks-' | Set-Content $_.FullName -NoNewline
}
```

Re-run `kubectl kustomize shopcloud/manifests/overlays/dev` before apply.

## References

- Architecture-aligned checks: [`../docs/deployment-verification.md`](../docs/deployment-verification.md)
