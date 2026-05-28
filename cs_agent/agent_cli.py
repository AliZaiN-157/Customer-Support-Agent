import functools
import os
import weave
from google.genai import types
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from toolbox_core import ToolboxSyncClient

from google.adk.sessions import InMemorySessionService
import asyncio
from dotenv import load_dotenv
from memory import search_memory, save_memory
from prompts import PROMPT_INSTRUCTION

load_dotenv()

# Set W&B API key from .env if available (avoids interactive login prompt)
wandb_key = os.getenv("WANDB_API_KEY")
if wandb_key:
    os.environ["WANDB_API_KEY"] = wandb_key

weave.init("customer-support-agent")

APP_NAME = "agents"
USER_ID = "demo_cli"

toolbox_client = ToolboxSyncClient(
    url="http://127.0.0.1:5000"
)

database_tools = toolbox_client.load_toolset("cs_agent_tools")

# Wrap each tool with Weave tracing so toolbox calls appear in the trace tree
for tool in database_tools:
    original_call = tool.__call__
    tool_name = tool.__name__

    @functools.wraps(original_call)
    @weave.op(name=tool_name)
    def traced_call(*args, _original=original_call, **kwargs):
        return _original(*args, **kwargs)

    tool.__call__ = traced_call

NEW_PROMPT_INSTRUCTION = PROMPT_INSTRUCTION.format(USER_ID=USER_ID)

root_agent = Agent(
    model='gemini-3.5-flash',
    name='customer_support_assistant',
    description=(
        'An expert customer support agent helping users with order-related questions and requests. '
        'Provides fast, clear, and friendly assistance with memory of past interactions.'
    ),
    instruction=NEW_PROMPT_INSTRUCTION,
    tools=[*database_tools, search_memory],
)

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


@weave.op()
async def run_agent(user_input: str) -> str:
    """Process a single user message through the agent and return the response."""
    content = types.Content(role='user', parts=[types.Part(text=user_input)])
    response = runner.run(user_id=USER_ID, session_id=f"session_{USER_ID}", new_message=content)

    final_response = ""
    for event in response:
        if event.is_final_response() and event.content:
            final_response = event.content.parts[0].text
    return final_response


@weave.op()
async def main():
    """Main chat loop with Weave observability."""
    messages = []
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=f"session_{USER_ID}")

    while True:
        print("=" * 80)
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
            break
        messages.append({"role": "user", "content": user_input})

        response_text = await run_agent(user_input)

        if response_text:
            print("Agent: ", response_text)
            messages.append({"role": "assistant", "content": response_text})

    save_memory(messages, USER_ID)
    toolbox_client.close()


if __name__ == "__main__":
    asyncio.run(main())
