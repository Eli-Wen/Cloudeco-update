data "google_project" "current" {
  project_id = "cloudeco-devops"
}

resource "google_storage_bucket" "terraform_state" {
  name                        = "cloudeco-devops-tfstate-${data.google_project.current.number}"
  location                    = "AUSTRALIA-SOUTHEAST1"
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }
}
