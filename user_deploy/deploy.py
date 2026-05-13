import os
import google.auth
import vertexai
import vertexai.agent_engines as ae
from vertexai.agent_engines import ModuleAgent

# Dynamically resolve active project ID
_, credentials_project_id = google.auth.default()
PROJECT_ID = credentials_project_id or "langchain-otel-1778262944"
LOCATION = "us-central1"
STAGING_BUCKET = f"gs://{PROJECT_ID}-staging"

print(f"Initializing Vertex AI SDK for project {PROJECT_ID}...")
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

# 1. Define the module-based agent (pickless deployment)
print("Defining ModuleAgent configuration...")
local_agent = ModuleAgent(
    module_name="agent_src.agent",
    agent_name="root_agent",
    register_operations={"": ["query"]},
)

# 2. Package and Register in Cloud
print("Deploying agent to Vertex AI Reasoning Engine from source packages...")
remote_agent = ae.create(
    agent_engine=local_agent,
    requirements="agent_src/requirements.txt",
    extra_packages=["agent_src"],
    display_name="LangChain OTel Traced Agent",
)

print(f"Agent deployed successfully!")
print(f"Reasoning Engine Resource ID: {remote_agent.resource_name}")

# Write target deployment metadata to a file for quick testing
with open("agent_metadata.txt", "w") as f:
    f.write(remote_agent.resource_name)
