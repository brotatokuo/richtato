"""Views for AI assistant chat and conversation management."""

import json

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from loguru import logger

from .models import Conversation
from .serializers import (
    ChatRequestSerializer,
    ConversationDetailSerializer,
    ConversationSerializer,
)
from .services.agent_service import AgentService


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    """Stream a chat response via Server-Sent Events.

    POST /api/v1/assistant/chat/
    Body: {"conversation_id": "uuid" | null, "message": "..."}
    Response: text/event-stream
    """
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    conversation_id = serializer.validated_data.get("conversation_id")
    user_message = serializer.validated_data["message"]

    agent_svc = AgentService(request.user)
    conversation = agent_svc.get_or_create_conversation(conversation_id)

    def event_stream():
        try:
            for event in agent_svc.invoke_stream(conversation, user_message):
                event_type = event.get("type", "token")
                if event_type == "token":
                    yield _sse_event("token", {"content": event["content"]})
                elif event_type == "tool_call":
                    yield _sse_event(
                        "tool_call",
                        {"name": event["name"], "args": event.get("args", {})},
                    )
                elif event_type == "error":
                    yield _sse_event("error", {"content": event["content"]})
                elif event_type == "done":
                    yield _sse_event(
                        "done",
                        {"conversation_id": event["conversation_id"]},
                    )
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield _sse_event("error", {"content": "An unexpected error occurred."})
            yield _sse_event("done", {"conversation_id": str(conversation.id)})

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    """List user's conversations, most recent first.

    GET /api/v1/assistant/conversations/
    """
    conversations = Conversation.objects.filter(user=request.user)
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def conversation_detail(request, pk):
    """Get or delete a conversation.

    GET /api/v1/assistant/conversations/<pk>/
    DELETE /api/v1/assistant/conversations/<pk>/
    """
    try:
        conversation = Conversation.objects.get(id=pk, user=request.user)
    except Conversation.DoesNotExist:
        return Response(
            {"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "DELETE":
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ConversationDetailSerializer(conversation)
    return Response(serializer.data)
