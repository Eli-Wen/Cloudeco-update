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
