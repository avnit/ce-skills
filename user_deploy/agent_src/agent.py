from typing import Dict, Any
import logging
from . import telemetry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("my_traced_agent")

class MyTracedAgent:
    """A standard LangChain agent designed to run on Vertex AI Reasoning Engine with OTel and Lazy Imports."""

    def __init__(self, model_name: str = "gemini-2.5-flash", service_name: str = "langchain-otel-agent"):
        self.model_name = model_name
        self.service_name = service_name
        
        # 1. Wheres up direct OpenTelemetry connectivity
        telemetry.set_opentelemetry(self.service_name)

    def set_up(self) -> None:
        """This method runs once inside the serverless runtime on cold boot."""
        # Lazy imports to decouple local serialization from workstation dependencies
        from langchain_google_vertexai import ChatVertexAI
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.tools import tool

        # Define tool inside boot lifecycle
        @tool
        def calculate_length(text: str) -> int:
            """Calculates the character length of a given text string."""
            return len(text)

        # Configure Chat model
        self.llm = ChatVertexAI(model_name=self.model_name, temperature=0)
        
        # Gather tools
        self.tools = [calculate_length]
        
        # Construct prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful agent with access to calculation tools."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Build agent
        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    @telemetry.do_trace(span_name="agent.execute_query")
    def query(self, input_text: str) -> Dict[str, Any]:
        """Executes an incoming query against the LangChain agent executor."""
        logger.info("Received incoming user query: %s", input_text)
        
        # Run the agent
        response = self.executor.invoke({"input": input_text})
        return response

# Module-level instantiation for direct cloud source loading
root_agent = MyTracedAgent()
