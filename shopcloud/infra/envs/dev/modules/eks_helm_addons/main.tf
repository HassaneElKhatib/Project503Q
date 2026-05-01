resource "helm_release" "aws_load_balancer_controller" {
  name             = "aws-load-balancer-controller"
  namespace        = "kube-system"
  repository       = "https://aws.github.io/eks-charts"
  chart            = "aws-load-balancer-controller"
  version          = var.aws_lb_controller_chart_version
  wait             = true
  timeout          = 1200
  create_namespace = false

  values = [yamlencode({
    clusterName = var.cluster_name
    region      = var.aws_region
    vpcId       = var.vpc_id
    replicaCount = 1
    enableServiceMutatorWebhook = false
    serviceAccount = {
      create = true
      annotations = {
        "eks.amazonaws.com/role-arn" = var.alb_controller_role_arn
      }
    }
  })]
}

resource "helm_release" "external_secrets" {
  count            = var.enable_external_secrets ? 1 : 0
  name             = "external-secrets"
  namespace        = "external-secrets-system"
  repository       = "https://charts.external-secrets.io"
  chart            = "external-secrets"
  version          = var.external_secrets_chart_version
  wait             = true
  timeout          = 1800
  create_namespace = true

  values = [yamlencode({
    installCRDs = true
    serviceAccount = {
      create = true
      annotations = {
        "eks.amazonaws.com/role-arn" = var.external_secrets_role_arn
      }
    }
    webhook = {
      port = 9443
    }
  })]

  depends_on = [helm_release.aws_load_balancer_controller, helm_release.metrics_server]
}

resource "helm_release" "metrics_server" {
  name             = "metrics-server"
  namespace        = "kube-system"
  repository       = "https://kubernetes-sigs.github.io/metrics-server"
  chart            = "metrics-server"
  version          = var.metrics_server_chart_version
  wait             = true
  timeout          = 1200
  create_namespace = false

  values = [yamlencode({
    args = ["--kubelet-insecure-tls"]
  })]

  depends_on = [helm_release.aws_load_balancer_controller]
}

resource "helm_release" "cluster_autoscaler" {
  count            = var.enable_cluster_autoscaler ? 1 : 0
  name             = "cluster-autoscaler"
  namespace        = "kube-system"
  repository       = "https://kubernetes.github.io/autoscaler"
  chart            = "cluster-autoscaler"
  version          = var.cluster_autoscaler_chart_version
  wait             = true
  timeout          = 1800
  create_namespace = false

  values = [yamlencode({
    autoDiscovery = {
      clusterName = var.cluster_name
      enabled     = true
    }
    awsRegion = var.aws_region
    rbac = {
      serviceAccount = {
        create = true
        annotations = {
          "eks.amazonaws.com/role-arn" = var.cluster_autoscaler_role_arn
        }
      }
    }
    extraArgs = {
      "balance-similar-node-groups" = true
    }
  })]

  depends_on = [helm_release.aws_load_balancer_controller, helm_release.metrics_server]
}
