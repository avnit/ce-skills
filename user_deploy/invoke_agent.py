import os
import google.auth
import vertexai
from vertexai.preview.reasoning_engines import ReasoningEngine

# Dynamically resolve active project ID
_, credentials_project_id = google.auth.default()
PROJECT_ID = credentials_project_id or "langchain-otel-1778262944"
LOCATION = "us-central1"

print(f"Initializing Vertex AI SDK for project {PROJECT_ID}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

resource_name = "projects/1051982776963/locations/us-central1/reasoningEngines/7540139031741333504"

print(f"Connecting to remote agent: {resource_name}")
remote_agent = ReasoningEngine(resource_name)

# Query requiring tool call: 'calculate_length'
query_text = "What is the character length of the word 'Supercalifragilisticexpialidocious'?"
print(f"Sending query: {query_text}")

response = remote_agent.query(input_text=query_text)

print("\nAgent Response:")
print(response)
