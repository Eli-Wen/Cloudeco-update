resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "cloudeco-images"
  description   = "CloudEco container images tagged with Git commit SHA."
  format        = "DOCKER"

  depends_on = [google_project_service.required["artifactregistry.googleapis.com"]]
}
