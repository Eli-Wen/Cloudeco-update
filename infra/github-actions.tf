data "google_project" "current" {
  project_id = var.project_id
}

# GitHub Actions exchanges its OIDC token for short-lived Google credentials.
# The pool/provider do not grant resource access by themselves; IAM bindings below do.
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "cloudeco-github"
  display_name              = "CloudEco GitHub Actions"
  description               = "Federated identities issued by GitHub Actions for CloudEco delivery."

  depends_on = [google_project_service.required["iam.googleapis.com"]]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub Actions OIDC"
  description                        = "Accepts OIDC tokens only from the configured CloudEco repository."

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }

  attribute_condition = "assertion.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "github_actions_deployer" {
  account_id   = "cloudeco-github-deployer"
  display_name = "CloudEco GitHub Actions deployer"
  description  = "Short-lived deployment identity impersonated by the trusted GitHub repository."

  depends_on = [google_project_service.required["iam.googleapis.com"]]
}

resource "google_service_account_iam_member" "github_actions_workload_identity" {
  service_account_id = google_service_account.github_actions_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/attribute.repository/${var.github_repository}"
}

# The workflow may push only to CloudEco's existing Docker repository.
resource "google_artifact_registry_repository_iam_member" "github_actions_writer" {
  project    = var.project_id
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.github_actions_deployer.email}"
}

# GKE's predefined developer role permits the workflow to update Kubernetes API objects.
resource "google_project_iam_member" "github_actions_gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.github_actions_deployer.email}"
}
