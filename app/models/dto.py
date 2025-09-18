from datetime import datetime

class ChatDTO:
    def __init__(self, id: int, user_id: str, created_at: datetime, updated_at: datetime):
        self.id = id
        self.user_id = user_id
        self.created_at = created_at
        self.updated_at = updated_at

class MessageDTO:
    def __init__(self, id: int, chat_id: int, role: str, text: str, timestamp: datetime):
        self.id = id
        self.chat_id = chat_id
        self.role = role
        self.text = text
        self.timestamp = timestamp
