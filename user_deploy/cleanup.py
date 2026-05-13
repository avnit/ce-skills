import os
import google.auth
import vertexai
import vertexai.agent_engines as ae

# Dynamically resolve active project ID
_, credentials_project_id = google.auth.default()
PROJECT_ID = credentials_project_id or "langchain-otel-1778262944"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

resource_name = "projects/1051982776963/locations/us-central1/reasoningEngines/7540139031741333504"

print(f"Deleting Reasoning Engine resource: {resource_name}")
ae.delete(resource_name)
print("Reasoning Engine resource deleted successfully!")
