# Sample Vulnerable Infrastructure configuration file for pre-sales security testing.

resource "google_storage_bucket" "customer_records" {
  name     = "acme-customer-records-bucket"
  location = "us-central1"
  
  # VULNERABILITY: Missing uniform_bucket_level_access (defaults to false/ACLs enabled)
  # uniform_bucket_level_access = true
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
