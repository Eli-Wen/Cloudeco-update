resource "google_service_account" "gke_nodes" {
  account_id   = "cloudeco-gke-nodes"
  display_name = "CloudEco GKE worker nodes"

  depends_on = [google_project_service.required["iam.googleapis.com"]]
}

locals {
  gke_node_roles = toset([
    "roles/artifactregistry.reader",
    "roles/container.defaultNodeServiceAccount",
  ])
}

resource "google_project_iam_member" "gke_nodes" {
  for_each = local.gke_node_roles

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_service_account" "grafana_datasource_syncer" {
  account_id   = "cloudeco-grafana-syncer"
  display_name = "CloudEco Grafana datasource syncer"

  depends_on = [google_project_service.required["iam.googleapis.com"]]
}

locals {
  grafana_datasource_syncer_roles = toset([
    "roles/monitoring.viewer",
    "roles/iam.serviceAccountTokenCreator",
  ])
}

resource "google_project_iam_member" "grafana_datasource_syncer" {
  for_each = local.grafana_datasource_syncer_roles

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.grafana_datasource_syncer.email}"
}

resource "google_service_account_iam_member" "grafana_datasource_syncer_workload_identity" {
  service_account_id = google_service_account.grafana_datasource_syncer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[observability/grafana-datasource-syncer]"
}
