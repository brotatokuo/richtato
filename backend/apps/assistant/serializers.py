"""Serializers for AI assistant API."""

from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "tool_calls", "created_at"]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at", "message_count"]
        read_only_fields = fields

    def get_message_count(self, obj):
        return obj.messages.count()


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at", "messages"]
        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(max_length=4000)
