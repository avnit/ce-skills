"""Custom Customer Engineer (CE) Campaign Agent with Native CSA Integration."""

from absl import logging
from google3.apps.intelligence.context.context_engine.lib.api import context_service_pb2
from google3.apps.intelligence.context.context_engine.lib.api import corpus_pb2
from google3.apps.intelligence.gen_ai.agency.common.python import py_base_workspace_agent
from google3.assistant.bard.agents.framework.agents.experimental.context_service import context_service_agent
from google3.assistant.bard.agents.framework.proto import agent_pb2
from google3.assistant.bard.agents.framework.proto import message_pb2
from google3.assistant.bard.agents.framework.proto.workspace import context_service_agent_config_pb2
from google3.learning.gemini.format.python import roles


class CeCampaignAgent(py_base_workspace_agent.WorkspaceBaseAgent):
  """CE Campaign Agent that leverages native ContextServiceAgent for account research."""

  def __init__(self, config: agent_pb2.AgentConfig):
    super().__init__(config)
    # Initialize underlying ContextServiceAgent as a sub-agent
    self._csa_sub_agent = context_service_agent.ContextServiceAgent(config)

  def _construct_csa_request(self, account_name: str, prompt: str) -> context_service_pb2.ContextServiceRequest:
    """Constructs a typed ContextServiceRequest proto for customer research."""
    request = context_service_pb2.ContextServiceRequest()
    
    # Configure Corpora Scope (GMAIL, DRIVE, CALENDAR, CHAT, KEEP)
    request.allowed_corpora.corpora.extend([
        corpus_pb2.Corpus.CORPUS_GMAIL,
        corpus_pb2.Corpus.CORPUS_DRIVE,
        corpus_pb2.Corpus.CORPUS_CALENDAR,
        corpus_pb2.Corpus.CORPUS_CHAT,
        corpus_pb2.Corpus.CORPUS_KEEP,
    ])
    
    # Set Latency Budget & Iteration Limits
    request.latency_budget_seconds = 40
    request.max_implicit_context_iterations = 5
    
    # Populate System Prompt & User Intent
    full_prompt = f"Perform deep account research for enterprise customer {account_name}. Focus on: {prompt}"
    request.prompt.agency_messages.messages.add(
        role=roles.ROLE_SYSTEM_1,
        chunks=[message_pb2.Chunk(text=full_prompt)]
    )
    return request

  def execute_account_research(self, account_name: str, research_intent: str) -> str:
    """Executes native CSA retrieval and returns grounded context with citations."""
    logging.info("Initiating native CSA research for account: %s", account_name)
    csa_request = self._construct_csa_request(account_name, research_intent)

    # Construct AgentCallEvent for RPC-style sub-agent invocation
    event = agent_pb2.AgentCallEvent()
    message = event.messages.add(role=roles.ROLE_USER)
    chunk = message.chunks.add(kind=message_pb2.Chunk.Kind.APPLICATION_DATA)
    chunk.application_data.Extensions[context_service_pb2.ContextServiceRequest.ext].CopyFrom(csa_request)

    # Invoke ContextServiceAgent natively
    csa_response_event = self._csa_sub_agent.Process(event)

    # Parse structured ContextServiceResponse
    if not csa_response_event.messages:
      return "No historical context found."

    # Extract verbalized context and structured citations
    verbalized_context = ""
    citations_summary = []
    
    for msg in csa_response_event.messages:
      for chk in msg.chunks:
        if chk.HasField("text"):
          verbalized_context += chk.text
        elif chk.WhichOneof("value") == "application_data" and chk.application_data.HasExtension(context_service_pb2.ContextServiceResponse.ext):
          response_proto = chk.application_data.Extensions[context_service_pb2.ContextServiceResponse.ext]
          for citation in response_proto.citations:
            citations_summary.append(f"- [{citation.file.metadata.title}]({citation.original_url or citation.file.guri})")

    formatted_output = f"### Research Findings for {account_name}\n\n{verbalized_context}\n\n### Key Citations\n" + "\n".join(citations_summary)
    return formatted_output
