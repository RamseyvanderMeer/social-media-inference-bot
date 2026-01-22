"""Pydantic models for X data structures."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class User(BaseModel):
    """User profile model."""

    id: str
    username: str
    followers: int = Field(ge=0)


class Post(BaseModel):
    """Post model."""

    id: str
    user_id: str
    username: str
    content: str
    timestamp: str
    likes: int = Field(ge=0, default=0)
    retweets: int = Field(ge=0, default=0)
    replies: int = Field(ge=0, default=0)
    is_thread: bool = False
    thread_id: Optional[str] = None
    is_sarcastic: bool = False
    topic: Optional[str] = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp format."""
        try:
            datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {v}") from e
        return v

    def to_document(self) -> str:
        """Convert post to document string for indexing."""
        metadata = f"[{self.username}] {self.timestamp}"
        if self.topic:
            metadata += f" | Topic: {self.topic}"
        if self.is_sarcastic:
            metadata += " | Sarcastic"
        return f"{metadata}\n{self.content}"


class Thread(BaseModel):
    """Thread model containing multiple posts."""

    thread_id: str
    posts: List[Post]
    user_id: str
    username: str
    topic: Optional[str] = None

    @property
    def full_content(self) -> str:
        """Get full thread content."""
        return "\n\n".join(post.content for post in self.posts)

    def to_document(self) -> str:
        """Convert thread to document string for indexing."""
        header = f"Thread by {self.username} ({len(self.posts)} posts)"
        if self.topic:
            header += f" | Topic: {self.topic}"
        return f"{header}\n\n{self.full_content}"


class Dataset(BaseModel):
    """Complete dataset model."""

    metadata: dict
    posts: List[Post]

    def get_threads(self) -> List[Thread]:
        """Extract threads from posts."""
        threads_dict: dict[str, List[Post]] = {}
        for post in self.posts:
            if post.thread_id:
                if post.thread_id not in threads_dict:
                    threads_dict[post.thread_id] = []
                threads_dict[post.thread_id].append(post)

        threads = []
        for thread_id, posts in threads_dict.items():
            # Sort posts by timestamp
            posts.sort(key=lambda p: p.timestamp)
            if posts:
                first_post = posts[0]
                thread = Thread(
                    thread_id=thread_id,
                    posts=posts,
                    user_id=first_post.user_id,
                    username=first_post.username,
                    topic=first_post.topic,
                )
                threads.append(thread)

        return threads

    def get_posts_by_topic(self, topic: str) -> List[Post]:
        """Get all posts for a specific topic."""
        return [post for post in self.posts if post.topic == topic]

    def get_sarcastic_posts(self) -> List[Post]:
        """Get all sarcastic posts."""
        return [post for post in self.posts if post.is_sarcastic]
