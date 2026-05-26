import re

content = """
resource "google_storage_bucket" "customer_records" {
  name     = "acme-customer-records-bucket"
  location = "us-central1"
}
"""

resource_type = "google_storage_bucket"
pattern = re.compile(r'resource\s+"' + resource_type + r'"\s+"([^"]+)"\s*\{')

match = pattern.search(content)
if match:
    print("Match found:", match.group(1))
else:
    print("No match found.")
