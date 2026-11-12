provider "google" {
  project = "cloudeco-devops"
  region  = "australia-southeast1"
}

# google_project_service_identity is currently exposed by the beta provider.
# It makes the GKE service agent a Terraform dependency before cluster creation.
provider "google-beta" {
  project = "cloudeco-devops"
  region  = "australia-southeast1"
}
