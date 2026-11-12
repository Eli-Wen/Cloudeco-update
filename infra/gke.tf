resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region

  network    = google_compute_network.gke.id
  subnetwork = google_compute_subnetwork.gke.id

  node_locations      = var.node_zones
  deletion_protection = false

  release_channel {
    channel = "REGULAR"
  }

  control_plane_endpoints_config {
    dns_endpoint_config {
      allow_external_traffic = true
    }

    ip_endpoints_config {
      enabled = false
    }
  }

  private_cluster_config {
    enable_private_nodes   = true
    master_ipv4_cidr_block = var.master_ipv4_cidr
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = "cloudeco-pods"
    services_secondary_range_name = "cloudeco-services"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
  }

  resource_labels = {
    project = "cloudeco"
    managed = "terraform"
  }

  depends_on = [
    google_project_service.required["compute.googleapis.com"],
    google_project_iam_member.gke_service_agent,
  ]
}

resource "google_container_node_pool" "workers" {
  name       = var.node_pool_name
  location   = google_container_cluster.primary.location
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count_per_zone

  node_locations = var.node_zones

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type    = var.node_machine_type
    image_type      = "COS_CONTAINERD"
    disk_type       = "pd-balanced"
    disk_size_gb    = 50
    service_account = google_service_account.gke_nodes.email
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]
    tags            = ["cloudeco-gke-node"]

    labels = {
      workload = "cloudeco"
    }

    metadata = {
      disable-legacy-endpoints = "true"
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  depends_on = [
    google_project_iam_member.gke_nodes,
    google_project_service.required["container.googleapis.com"],
  ]
}
