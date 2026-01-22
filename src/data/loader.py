"""Load and parse mock X dataset into structured format."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from src.data.models import Dataset, Post

logger = logging.getLogger(__name__)


class DataLoader:
    """Load and parse X dataset from JSON."""

    def __init__(self, data_path: Path):
        """Initialize loader with data path."""
        self.data_path = Path(data_path)
        self.dataset: Optional[Dataset] = None

    def load(self) -> Dataset:
        """Load dataset from JSON file."""
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Data file not found: {self.data_path}. "
                "Run data generator first."
            )

        logger.info(f"Loading dataset from {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate and parse posts
        posts = [Post(**post_data) for post_data in data.get("posts", [])]

        dataset = Dataset(
            metadata=data.get("metadata", {}),
            posts=posts,
        )

        self.dataset = dataset
        logger.info(
            f"Loaded {len(posts)} posts from dataset. "
            f"Metadata: {dataset.metadata}"
        )

        return dataset

    def get_all_posts(self) -> List[Post]:
        """Get all posts from loaded dataset."""
        if self.dataset is None:
            self.load()
        return self.dataset.posts if self.dataset else []

    def get_all_documents(self) -> List[str]:
        """Get all posts as document strings for indexing."""
        posts = self.get_all_posts()
        return [post.to_document() for post in posts]

    def get_metadata(self) -> dict:
        """Get dataset metadata."""
        if self.dataset is None:
            self.load()
        return self.dataset.metadata if self.dataset else {}


def load_dataset(data_path: Path = Path("data/mock_x_data.json")) -> Dataset:
    """Convenience function to load dataset."""
    loader = DataLoader(data_path)
    return loader.load()
