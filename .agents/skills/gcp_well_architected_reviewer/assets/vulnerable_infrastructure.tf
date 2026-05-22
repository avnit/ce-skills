# Sample Vulnerable Infrastructure configuration file for pre-sales security testing.

resource "google_storage_bucket" "customer_records" {
  name     = "acme-customer-records-bucket"
  location = "us-central1"
  
  # VULNERABILITY: Missing uniform_bucket_level_access (defaults to false/ACLs enabled)
  # uniform_bucket_level_access = true

  # VULNERABILITY: Missing encryption block (CMEK not enforced)
  # encryption {
  #   default_kms_key_name = "kms-key"
  # }
}

resource "google_kms_crypto_key" "app_encryption_key" {
  name            = "acme-app-crypto-key"
  key_ring        = "acme-keyring"
  
  # VULNERABILITY: Missing rotation_period
  # rotation_period = "7776000s"
}

resource "google_project_iam_binding" "project_viewer_access" {
  project = "acme-corp-prod-99"
  role    = "roles/viewer"

  # VULNERABILITY: Wildcard public member access
  members = [
    "user:admin@acmecorp.com",
    "allUsers"
  ]
}

resource "google_compute_firewall" "allow_ssh_public" {
  name    = "allow-ssh-public"
  network = "default"

  # VULNERABILITY: Open SSH ingress port 22 from all IP addresses
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_bigquery_dataset_access" "public_dataset" {
  dataset_id = "acme_raw_data"
  role       = "READER"

  # VULNERABILITY: Public BQ dataset access
  special_group = "allUsers"
}

resource "google_sql_database_instance" "acme_db" {
  name             = "acme-prod-db"
  database_version = "POSTGRES_15"
  region           = "us-central1"

  settings {
    tier = "db-custom-1-3840"
    
    # VULNERABILITY: Missing backup_configuration block (disabled database backups)
  }
}

resource "google_container_cluster" "gke_cluster" {
  name     = "acme-gke-cluster"
  location = "us-central1"

  # VULNERABILITY: Missing private_cluster_config (public worker nodes exposed)
}

resource "google_compute_subnetwork" "subnet_a" {
  name          = "acme-subnet-a"
  ip_cidr_range = "10.0.1.0/24"
  region        = "us-central1"
  network       = "acme-vpc"

  # VULNERABILITY: Missing log_config block (disabled VPC Flow Logs)
}
