"""Bedrock adapter that mimics the OpenAI chat completions interface.

IntentParser calls:
    client.chat.completions.create(model=..., messages=[...])
and reads:
    response.choices[0].message.content

This adapter wraps boto3's bedrock-runtime converse API to match that shape.
"""
from __future__ import annotations

import boto3


class _Message:
    def __init__(self, content: str) -> None:
        self.content = content


class _Choice:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _Response:
    def __init__(self, content: str) -> None:
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self, bedrock_client, model_id: str) -> None:
        self._client = bedrock_client
        self._model_id = model_id

    def create(self, model: str, messages: list[dict]) -> _Response:
        # Convert OpenAI-style messages to Bedrock converse format
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_parts = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in messages
            if m["role"] != "system"
        ]

        kwargs: dict = {
            "modelId": self._model_id,
            "messages": user_parts,
        }
        if system_parts:
            kwargs["system"] = [{"text": "\n".join(system_parts)}]

        response = self._client.converse(**kwargs)
        content = response["output"]["message"]["content"][0]["text"]
        return _Response(content)


class _Chat:
    def __init__(self, bedrock_client, model_id: str) -> None:
        self.completions = _Completions(bedrock_client, model_id)


class BedrockClient:
    """Drop-in replacement for openai.OpenAI() for use with IntentParser."""

    def __init__(self, model_id: str = "amazon.nova-micro-v1:0", region: str = "us-east-1") -> None:
        self._boto_client = boto3.client("bedrock-runtime", region_name=region)
        self.chat = _Chat(self._boto_client, model_id)
