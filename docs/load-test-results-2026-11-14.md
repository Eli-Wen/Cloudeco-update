# 2026-11-14 阶段 2 负载与可观测性验证

## 测试范围

- 压测发起端：集群内 Locust Job。
- 场景：60 个并发用户，10 users/s 启动，运行 8 分钟。
- 被测路由：`POST /api/predict` 与 `POST /api/annotate`。
- 请求链路：Locust -> `cloudeco-api` ClusterIP Service -> API Pod。
- 观测链路：API `/metrics` -> Google Managed Prometheus -> Grafana。

## Locust 结果

| 路由 | 请求数 | 失败数 | 中位延迟 | P95 | P99 | 平均延迟 | 结束时 RPS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `/api/annotate` | 973 | 0 | 8.1 s | 11 s | 12 s | 8.18 s | 3.5 |
| `/api/predict` | 951 | 0 | 8.1 s | 11 s | 12 s | 8.38 s | 2.8 |
| 汇总 | 1,924 | 0 | 8.1 s | 11 s | 12 s | 8.28 s | 6.3 |

## Grafana 与 GKE 观测

- Grafana 面板已展示两条 API 路由的 RPS、端到端 P50/P95/P99、YOLO 各阶段 P95、HPA 副本数、每 Pod CPU 与内存。
- 本轮没有 Locust 失败；错误率面板没有时间序列，符合没有记录到 API 错误的结果。
- HPA 的 current/desired replicas 从 4 扩至 6。
- API Pod CPU 峰值接近 1 core；主要工作 Pod 的内存约为 1.0--1.3 GiB，低于 3 GiB limit。
- YOLO inference 的 P95 约 0.9 s；端到端 P95 为 11 s，说明高并发下的主要尾延迟来自请求排队，而不是预处理或后处理。

## 结论与边界

本阶段已在云上验证可观测性闭环和 HPA 扩容：能够把压测流量、端到端延迟、推理阶段耗时、资源使用和副本变化放到同一时间轴分析。

该轮在 60 用户下实现零失败与约 6.3 RPS，但 P95 仍为 11 s；这不是可宣称的生产低延迟 SLA，而是后续容量和架构优化的已记录基线。
