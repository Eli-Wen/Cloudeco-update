variable "project_id" {
  description = "Existing GCP project that owns the CloudEco infrastructure."
  type        = string
  default     = "cloudeco-devops"
}

variable "region" {
  description = "Single GCP region for the regional GKE cluster."
  type        = string
  default     = "australia-southeast1"
}

variable "node_zones" {
  description = "One worker node is placed in each zone."
  type        = list(string)
  default = [
    "australia-southeast1-a",
    "australia-southeast1-b",
    "australia-southeast1-c",
  ]
}

variable "network_cidr" {
  description = "Primary IPv4 range for the GKE node subnet."
  type        = string
  default     = "10.20.0.0/20"
}

variable "pod_cidr" {
  description = "Secondary IPv4 range assigned to GKE Pods."
  type        = string
  default     = "10.24.0.0/16"
}

variable "service_cidr" {
  description = "Secondary IPv4 range assigned to Kubernetes Services."
  type        = string
  default     = "10.25.0.0/20"
}

variable "master_ipv4_cidr" {
  description = "Non-overlapping /28 range reserved for the private GKE control plane."
  type        = string
  default     = "172.16.0.0/28"
}

variable "cluster_name" {
  description = "GKE cluster name."
  type        = string
  default     = "cloudeco-gke"
}

variable "node_pool_name" {
  description = "GKE worker node-pool name."
  type        = string
  default     = "cloudeco-workers"
}

variable "node_machine_type" {
  description = "Verified machine type for each worker node."
  type        = string
  default     = "n2-custom-4-8192"
}

variable "node_count_per_zone" {
  description = "Fixed worker-node count in each selected zone."
  type        = number
  default     = 1
}

variable "github_repository" {
  description = "GitHub owner/repository allowed to obtain the CI/CD deployment identity."
  type        = string
  default     = "Eli-Wen/Cloudeco-update"
}
