# CloudEco GKE Terraform

本目录只声明 CloudEco 的 GCP 基础设施；执行 `apply` 前不会创建 GKE、Worker 或其他收费资源。

## 资源边界

- 单 Region：`australia-southeast1`（Sydney）。
- GKE Standard Regional：Google 托管多 Zone Control Plane。
- Worker：A、B、C 三个 Zone 各 1 台 `n2-custom-4-8192`，总计 3 台。
- Worker 没有公网 IP；镜像从 Artifact Registry 拉取时走 Private Google Access / Cloud NAT 的 HTTPS `:443` 出站链路。
- 业务入口不在本框创建：没有公网 Load Balancer、NodePort、域名或业务 TLS。
- 管理入口是 GKE DNS Control Plane Endpoint；管理员或后续 CI 通过 IAM 授权访问 TLS `:443`。

## 执行顺序

所有命令在 `infra/` 或其子目录执行。运行前确认已登录正确的 GCP 项目，且 Terraform 可取得 Application Default Credentials。

### 1. 建立远端 state bucket

首次执行时，state bucket 尚不存在，因此 `bootstrap-state/` 暂时使用本地 state。它只创建版本化、uniform bucket-level access 的 GCS bucket；这一动作会写入 GCP，必须在你批准后才运行 `apply`。

```powershell
terraform -chdir=bootstrap-state init
terraform -chdir=bootstrap-state validate
terraform -chdir=bootstrap-state plan -out=bootstrap.tfplan
# 审核 plan 后，才执行：
terraform -chdir=bootstrap-state apply bootstrap.tfplan
```

记录输出的 `terraform_state_bucket` 名称。不要提交 `bootstrap-state/terraform.tfstate`。

### 2. 配置主模块变量和 remote state

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init -backend-config="bucket=<terraform_state_bucket>"
terraform validate
terraform plan -out=cloudeco.tfplan
```

`terraform init` 连接 GCS state bucket；`validate` 只检查配置；`plan` 只向 GCP 查询并计算差异。三者不会创建 GKE Worker。不要把 `terraform.tfvars`、`.terraform/` 或 `*.tfplan` 提交到 Git。

### 3. 审核计划并等待明确批准

在 `apply` 前逐项核对：

1. Node pool 的总 Worker 数是 3，不是每 Zone 3 台。
2. 机器规格是 `n2-custom-4-8192`，磁盘是 50 GiB `pd-balanced`。
3. 计划只包含本项目的 VPC、Subnet、Router/NAT、Artifact Registry、节点 IAM、GKE 和启用的 API。
4. 当前配额、预算提醒和预期测试时间窗足以覆盖 GKE Regional、Worker、磁盘和网络费用。

只有得到明确批准，才执行：

```powershell
terraform apply cloudeco.tfplan
```

## 成功后给下一框的输出

`outputs.tf` 会输出集群名、Region、VPC、Subnet 和 Artifact Registry repository path。后续集群部署框使用：

```text
CI 或管理员
→ GKE DNS Endpoint，TLS :443，IAM 授权
→ Kubernetes API
→ Deployment 引用 Artifact Registry 的 Git-SHA 镜像
→ 私有 Worker 经 HTTPS :443 拉取镜像
→ Pod 内 Uvicorn 监听 :8000
→ ClusterIP Service :80 转发到 Pod :8000
```

本 Terraform 框不部署应用、Service、HPA、Locust、CI/CD 或监控规则；它只提供这些后续组件需要的私有网络、集群、镜像仓库和身份基础。
