import base64
import json
import zlib

class ChatShare:
    @staticmethod
    def serialize_chat(chat_history):
        minimal = [{"r": m["role"], "c": m["content"]} for m in chat_history]
        return json.dumps(minimal)

    @staticmethod
    def encode_chat(json_str):
        compressed = zlib.compress(json_str.encode("utf-8"))
        return base64.urlsafe_b64encode(compressed).decode("utf-8")

    @staticmethod
    def generate_share_link(chat_history):
        """Generate a compressed encoded payload for URL injection."""
        return ChatShare.encode_chat(ChatShare.serialize_chat(chat_history))

    @staticmethod
    def decode_chat(encoded: str) -> str:
        compressed = base64.urlsafe_b64decode(encoded.encode("utf-8"))
        return zlib.decompress(compressed).decode("utf-8")

    @staticmethod
    def deserialize_chat(json_str: str) -> list:
        minimal = json.loads(json_str)
        return [{"role": m["r"], "content": m["c"]} for m in minimal]

    @staticmethod
    def load_from_link(encoded: str) -> list:
        return ChatShare.deserialize_chat(ChatShare.decode_chat(encoded))
