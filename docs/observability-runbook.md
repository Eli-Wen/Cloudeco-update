# CloudEco observability runbook

## Purpose

Grafana is the shared-time-axis dashboard for a Locust load test. Cloud Logging remains the source for the individual error or restart that the dashboard exposes.

## Dashboard reading order

1. Check RPS and P95/P99 together. A rising P95 with flat RPS means requests are queueing.
2. Check the 5xx panel. If it rises, open Cloud Logging for the matching time range and request path.
3. Compare inference-stage P95 with end-to-end P95. If inference is much lower, the extra time is queueing or request processing.
4. Compare Pod CPU and memory with HPA current/desired replicas. This shows whether HPA reacted and whether the new replicas became capacity.

## Deployment order

1. Apply Terraform for the Grafana datasource-syncer identity and the GKE state-metric components.
2. Create the `grafana-admin-credentials` Secret in the `observability` namespace. Do not commit its password.
3. Apply the Grafana namespace, service accounts, PVC, provisioning, dashboard, Deployment, and Service.
4. Port-forward `service/grafana` to local port 3000 and sign in.
5. Create a Grafana service account with Data Sources Writer permission. Store its token in the `grafana-datasource-syncer-token` Secret.
6. Apply `datasource-syncer.yaml`. The initial Job and the 10-minute CronJob configure the `gmp` data source to query Google Managed Prometheus.
7. Open the `CloudEco Load Test Overview` dashboard and run Locust.

## Log escalation

Use Cloud Logging only after an observable signal is abnormal:

- 5xx rate rises: filter `path` and the test time range.
- Pod restart or memory rise: filter the Pod name and inspect OOM or traceback messages.
- Desired replicas exceed current replicas: inspect Kubernetes events for pending Pods or image pull delay.
