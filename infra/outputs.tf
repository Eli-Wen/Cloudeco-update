output "artifact_registry_repository" {
  description = "Docker repository path used by CI and GKE image pulls."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "cluster_name" {
  description = "Regional GKE cluster name."
  value       = google_container_cluster.primary.name
}

output "cluster_region" {
  description = "Region used by gcloud get-credentials."
  value       = google_container_cluster.primary.location
}

output "network_name" {
  description = "VPC name for CloudEco GKE."
  value       = google_compute_network.gke.name
}

output "subnetwork_name" {
  description = "Subnet name for CloudEco GKE nodes."
  value       = google_compute_subnetwork.gke.name
}
