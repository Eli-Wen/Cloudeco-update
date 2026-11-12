locals {
  required_services = toset([
    "artifactregistry.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
  ])
}

resource "google_project_service" "required" {
  for_each = local.required_services

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# Enabling an API and its Google-managed identity are asynchronous operations.
# Generate the GKE service identity first; the cluster must not race it.
resource "google_project_service_identity" "gke" {
  provider = google-beta

  project = var.project_id
  service = "container.googleapis.com"

  depends_on = [google_project_service.required["container.googleapis.com"]]
}

# GKE needs this Google-managed agent to manage nodes, disks, and load balancers.
# This is its documented standard role, not a role for a user or application SA.
resource "google_project_iam_member" "gke_service_agent" {
  project = var.project_id
  role    = "roles/container.serviceAgent"
  member  = google_project_service_identity.gke.member
}
