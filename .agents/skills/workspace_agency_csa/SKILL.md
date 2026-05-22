---
name: workspace-agency-csa
description: >-
  Use when instantiating, configuring, or invoking Google Workspace's ContextServiceAgent natively inside custom Python agents to perform cross-corpus semantic search across Gmail, Calendar, Drive, Chat, and Keep.
---

# Skill: Native Integration of ContextServiceAgent

This skill provides cheatsheet recipes and procedural gotchas for Customer Engineers (CEs) to directly invoke Google Workspace's **`ContextServiceAgent`** sub-agent natively in-memory. This bypasses process execution latency of CLI binaries (like `csa_cli.par`) and enables structured passing of Protocol Buffers containing multimodal grounding data and rich citations.

---

## Core Workflow

### 1. Import Proto and Agency Dependencies
Ensure your Python agent imports the correct API and corpus proto stubs.
*   *Reference*: See [build_dependencies.md](references/build_dependencies.md) for the required `BUILD` imports.

### 2. Construct the `ContextServiceRequest`
Create the request proto, specifying the allowed corpora scope, latency budgets, and iteration boundaries:
```python
from google3.apps.intelligence.context.context_engine.lib.api import context_service_pb2
from google3.apps.intelligence.context.context_engine.lib.api import corpus_pb2

request = context_service_pb2.ContextServiceRequest()

# Define Allowed Corpora (GMAIL, DRIVE, CALENDAR, CHAT, KEEP)
request.allowed_corpora.corpora.extend([
    corpus_pb2.Corpus.CORPUS_GMAIL,
    corpus_pb2.Corpus.CORPUS_DRIVE,
    corpus_pb2.Corpus.CORPUS_CALENDAR,
    corpus_pb2.Corpus.CORPUS_CHAT,
    corpus_pb2.Corpus.CORPUS_KEEP,
])

request.latency_budget_seconds = 40
request.max_implicit_context_iterations = 5
```

### 3. Invoke `ContextServiceAgent` Natively
Do not spawn a subprocess. Pass the request inside an `AgentCallEvent` to the sub-agent:
```python
from google3.assistant.bard.agents.framework.proto import agent_pb2
from google3.assistant.bard.agents.framework.proto import message_pb2

# Subclass your agent from WorkspaceBaseAgent and instantiate the sub-agent:
# self._csa_sub_agent = context_service_agent.ContextServiceAgent(config)

event = agent_pb2.AgentCallEvent()
message = event.messages.add(role=roles.ROLE_USER)
chunk = message.chunks.add(kind=message_pb2.Chunk.Kind.APPLICATION_DATA)
chunk.application_data.Extensions[context_service_pb2.ContextServiceRequest.ext].CopyFrom(request)

response_event = self._csa_sub_agent.Process(event)
```

### 4. Parse Chunks and Citation Metadata
Extract the parsed text chunks and structured citation links (`guri` or original URL):
```python
for msg in response_event.messages:
  for chk in msg.chunks:
    if chk.HasField("text"):
      print(f"Context: {chk.text}")
    elif chk.WhichOneof("value") == "application_data" and chk.application_data.HasExtension(context_service_pb2.ContextServiceResponse.ext):
      resp_proto = chk.application_data.Extensions[context_service_pb2.ContextServiceResponse.ext]
      for citation in resp_proto.citations:
        # Extract title and source URL/GURI natively
        print(f"Citation: [{citation.file.metadata.title}]({citation.original_url or citation.file.guri})")
```

---

## 💡 E2E Recipe: "Last 30 Days Account Review"

To generate a chronological interaction review of a customer account over the last 30 days, configure your query and process the output following this recipe:

1.  **Formulate the Prompt with Date Filtering**:
    `prompt = f"Find all emails, calendar invites, chat escalations, and shared blueprints regarding Customer {account_name} in the last 30 days."`
2.  **Execute Native Retrieval**: Pass the query using the GMR allowed corpora request block.
3.  **Chronological Timeline Assembly**:
    *   Filter the citations based on `citation.file.metadata.last_modified_timestamp` (or chronological date mentioned in Gmail threads).
    *   Format and present the output as a clean vertical timeline:
        `- [2026-05-01] meeting: Customer sync on GKE Filestore`
        `- [2026-05-05] email: escalation regarding STS permissions`

---

## 🛠️ Reference Materials
*   **BUILD Dependencies**: See [build_dependencies.md](references/build_dependencies.md)
*   **Python Reference Implementation**: See [ce_campaign_agent.py](references/ce_campaign_agent.py)
*   **Manual Presubmit Notebook**: See [testing_validation.md](references/testing_validation.md)

***

## Gotchas & Pitfalls

*   **LOAS / gcert Session Expiry**: GMR/LOAS API queries will fail silently or crash with credential errors if your local `gcert` session has expired. Always verify your `gcert` is active before initiating a run.
*   **Ephemeral Session Memory**: To align with `go/code-ai-policy`, **NEVER** cache raw customer PII or confidential Drive chunks in persistent, world-readable directories. Keep all retrieved context inside the ephemeral Jetski session memory.
