import weave
from mem0 import MemoryClient
from dotenv import load_dotenv
import os

load_dotenv()

mem0 = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))


@weave.op()
def search_memory(query: str, user_id: str) -> str:
    """Search memory for relevant past interactions."""
    filters = {"user_id": user_id}
    memories = mem0.search(query, filters=filters)
    if memories and memories.get("results"):
        result = memories["results"][0]
        if result and result.get("memory"):
            return f"Relevant memories: {result['memory']}"
    return "no_memories"


@weave.op()
def save_memory(messages, user_id: str):
    """Save conversation messages to memory."""
    if messages:
        messages_to_save = []
        for msg in messages:
            messages_to_save.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        mem0.add(messages_to_save, user_id=user_id)
