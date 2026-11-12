resource "google_compute_network" "gke" {
  name                    = "cloudeco-gke-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"

  depends_on = [google_project_service.required["compute.googleapis.com"]]
}

resource "google_compute_subnetwork" "gke" {
  name                     = "cloudeco-gke-subnet"
  ip_cidr_range            = var.network_cidr
  region                   = var.region
  network                  = google_compute_network.gke.id
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "cloudeco-pods"
    ip_cidr_range = var.pod_cidr
  }

  secondary_ip_range {
    range_name    = "cloudeco-services"
    ip_cidr_range = var.service_cidr
  }
}

resource "google_compute_router" "gke" {
  name    = "cloudeco-gke-router"
  region  = var.region
  network = google_compute_network.gke.id

  bgp {
    asn = 64514
  }
}

resource "google_compute_router_nat" "gke" {
  name                               = "cloudeco-gke-nat"
  router                             = google_compute_router.gke.name
  region                             = google_compute_router.gke.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}
