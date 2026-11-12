output "terraform_state_bucket" {
  description = "Pass this value to the main Terraform init command as the GCS backend bucket."
  value       = google_storage_bucket.terraform_state.name
}
