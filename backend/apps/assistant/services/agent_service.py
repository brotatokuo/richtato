"""Service that orchestrates the LangGraph agent invocation."""

import uuid
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from loguru import logger

from apps.assistant.graph.graph import build_graph
from apps.assistant.models import Conversation, Message
from apps.assistant.prompts.system import build_system_prompt


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


class AgentService:
    """Manages conversation state and invokes the LangGraph agent."""

    def __init__(self, user):
        self.user = user
        self.graph = _get_graph()

    def get_or_create_conversation(
        self, conversation_id: Optional[uuid.UUID] = None
    ) -> Conversation:
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id, user=self.user)
            except Conversation.DoesNotExist:
                pass
        return Conversation.objects.create(user=self.user)

    def _load_message_history(self, conversation: Conversation) -> list:
        """Reconstruct LangChain message objects from stored messages."""
        lc_messages = []
        for msg in conversation.messages.all():
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
        return lc_messages

    def _save_user_message(self, conversation: Conversation, content: str) -> Message:
        return Message.objects.create(
            conversation=conversation,
            role="user",
            content=content,
        )

    def _save_assistant_message(
        self, conversation: Conversation, content: str
    ) -> Message:
        return Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=content,
        )

    def _maybe_set_title(self, conversation: Conversation, user_message: str):
        """Auto-set conversation title from the first user message."""
        if not conversation.title:
            title = user_message[:80]
            if len(user_message) > 80:
                title = title.rsplit(" ", 1)[0] + "..."
            conversation.title = title
            conversation.save(update_fields=["title"])

    def invoke_stream(
        self,
        conversation: Conversation,
        user_message: str,
    ):
        """Invoke the agent and yield streaming events.

        Yields dicts with keys:
            - {"type": "token", "content": str}
            - {"type": "tool_call", "name": str, "args": dict}
            - {"type": "done", "conversation_id": str}
            - {"type": "error", "content": str}
        """
        self._save_user_message(conversation, user_message)
        self._maybe_set_title(conversation, user_message)

        system_prompt = build_system_prompt(self.user)
        history = self._load_message_history(conversation)

        messages = [SystemMessage(content=system_prompt)] + history

        config = {
            "configurable": {
                "user": self.user,
                "thread_id": str(conversation.id),
            }
        }

        try:
            full_response = ""
            for event in self.graph.stream(
                {"messages": messages},
                config=config,
                stream_mode="updates",
            ):
                for node_name, node_output in event.items():
                    if node_name == "agent":
                        ai_messages = node_output.get("messages", [])
                        for msg in ai_messages:
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    yield {
                                        "type": "tool_call",
                                        "name": tc["name"],
                                        "args": tc.get("args", {}),
                                    }
                            if msg.content:
                                full_response += msg.content
                                yield {"type": "token", "content": msg.content}

            if full_response:
                self._save_assistant_message(conversation, full_response)

            yield {"type": "done", "conversation_id": str(conversation.id)}

        except Exception as e:
            logger.error(f"Agent invocation error: {e}")
            error_msg = "I'm sorry, I encountered an error processing your request. Please try again."
            self._save_assistant_message(conversation, error_msg)
            yield {"type": "error", "content": error_msg}
            yield {"type": "done", "conversation_id": str(conversation.id)}
