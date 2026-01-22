"""Generate realistic mock X (Twitter) dataset with ambiguity scenarios."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


class XDataGenerator:
    """Generate mock X (Twitter) data with realistic features."""

    def __init__(self, seed: int = 42):
        """Initialize generator with random seed."""
        random.seed(seed)
        np.random.seed(seed)

        # Sample user profiles
        self.users = [
            {"id": f"user_{i}", "username": f"tech_user_{i}", "followers": random.randint(100, 100000)}
            for i in range(50)
        ]

        # Topics and keywords for generating content
        self.topics = [
            "AI", "machine learning", "Python", "JavaScript", "web development",
            "data science", "cloud computing", "cybersecurity", "blockchain",
            "startup", "venture capital", "productivity", "remote work",
        ]

        # Ambiguity scenarios templates
        self.sarcasm_templates = [
            "Oh great, another {topic} solution that will definitely work perfectly...",
            "Because {topic} is exactly what we needed right now.",
            "I'm so excited about {topic}. Can't wait for it to fail spectacularly.",
        ]

        self.conflicting_info_topics = [
            ("AI will replace all jobs", "AI will create more jobs than it replaces"),
            ("Remote work is the future", "Remote work is declining"),
            ("Python is the best language", "JavaScript is more versatile"),
        ]

    def generate_post(
        self,
        user: Dict,
        topic: str,
        is_sarcastic: bool = False,
        is_thread: bool = False,
        thread_id: Optional[str] = None,
    ) -> Dict:
        """Generate a single post."""
        base_time = datetime.now() - timedelta(days=random.randint(0, 30))
        timestamp = base_time + timedelta(
            seconds=random.randint(0, 86400)
        )

        if is_sarcastic:
            content = random.choice(self.sarcasm_templates).format(topic=topic)
        else:
            content = self._generate_realistic_content(topic)

        post = {
            "id": f"post_{random.randint(10000, 99999)}",
            "user_id": user["id"],
            "username": user["username"],
            "content": content,
            "timestamp": timestamp.isoformat(),
            "likes": random.randint(0, 10000),
            "retweets": random.randint(0, 1000),
            "replies": random.randint(0, 500),
            "is_thread": is_thread,
            "thread_id": thread_id,
            "is_sarcastic": is_sarcastic,
            "topic": topic,
        }

        return post

    def _generate_realistic_content(self, topic: str) -> str:
        """Generate realistic post content about a topic."""
        templates = [
            f"Just read an interesting article about {topic}. Thoughts?",
            f"Working on a {topic} project. Anyone have experience with this?",
            f"{topic} is evolving so fast. What do you think the next big thing will be?",
            f"Hot take: {topic} is overhyped. Change my mind.",
            f"New {topic} framework released. Has anyone tried it yet?",
            f"Debating whether to invest time in {topic}. Worth it?",
            f"{topic} conference was amazing! Key takeaways: [thread]",
            f"Building something cool with {topic}. Will share details soon.",
        ]
        return random.choice(templates)

    def generate_thread(
        self,
        user: Dict,
        topic: str,
        num_posts: int = 3,
    ) -> List[Dict]:
        """Generate a thread of connected posts."""
        thread_id = f"thread_{random.randint(10000, 99999)}"
        posts = []

        base_time = datetime.now() - timedelta(days=random.randint(0, 30))

        # Initial post
        initial_post = self.generate_post(
            user, topic, is_thread=True, thread_id=thread_id
        )
        initial_post["timestamp"] = base_time.isoformat()
        posts.append(initial_post)

        # Reply posts
        for i in range(1, num_posts):
            reply_time = base_time + timedelta(minutes=random.randint(1, 60))
            reply = self.generate_post(
                user, topic, is_thread=True, thread_id=thread_id
            )
            reply["timestamp"] = reply_time.isoformat()
            reply["content"] = f"Thread continuation {i}: {reply['content']}"
            posts.append(reply)

        return posts

    def generate_evolving_thread(
        self,
        user: Dict,
        topic: str,
        num_posts: int = 5,
    ) -> List[Dict]:
        """Generate a thread that evolves/changes direction."""
        thread_id = f"thread_{random.randint(10000, 99999)}"
        posts = []
        base_time = datetime.now() - timedelta(days=random.randint(0, 30))

        # Start with one perspective
        initial_post = self.generate_post(
            user, topic, is_thread=True, thread_id=thread_id
        )
        initial_post["timestamp"] = base_time.isoformat()
        initial_post["content"] = f"Initial thought: {initial_post['content']}"
        posts.append(initial_post)

        # Evolve the discussion
        evolution_steps = [
            "Update: After more research, I'm reconsidering...",
            "Actually, I think I was wrong about this. Here's why:",
            "New development: This changes everything.",
            "Final thoughts: After all this discussion...",
        ]

        for i, evolution in enumerate(evolution_steps[: num_posts - 1], 1):
            reply_time = base_time + timedelta(hours=random.randint(1, 24))
            reply = self.generate_post(
                user, topic, is_thread=True, thread_id=thread_id
            )
            reply["timestamp"] = reply_time.isoformat()
            reply["content"] = f"{evolution} {reply['content']}"
            posts.append(reply)

        return posts

    def generate_conflicting_posts(
        self,
        topic_pair: tuple,
        num_pairs: int = 3,
    ) -> List[Dict]:
        """Generate posts with conflicting information."""
        posts = []
        base_time = datetime.now() - timedelta(days=random.randint(0, 30))

        for i in range(num_pairs):
            user1 = random.choice(self.users)
            user2 = random.choice(self.users)

            # Post supporting first perspective
            post1 = {
                "id": f"post_{random.randint(10000, 99999)}",
                "user_id": user1["id"],
                "username": user1["username"],
                "content": topic_pair[0],
                "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                "likes": random.randint(0, 5000),
                "retweets": random.randint(0, 500),
                "replies": random.randint(0, 200),
                "is_thread": False,
                "thread_id": None,
                "is_sarcastic": False,
                "topic": "conflicting_info",
            }

            # Post supporting second perspective
            post2 = {
                "id": f"post_{random.randint(10000, 99999)}",
                "user_id": user2["id"],
                "username": user2["username"],
                "content": topic_pair[1],
                "timestamp": (base_time + timedelta(hours=i, minutes=30)).isoformat(),
                "likes": random.randint(0, 5000),
                "retweets": random.randint(0, 500),
                "replies": random.randint(0, 200),
                "is_thread": False,
                "thread_id": None,
                "is_sarcastic": False,
                "topic": "conflicting_info",
            }

            posts.extend([post1, post2])

        return posts

    def generate_dataset(
        self,
        num_posts: int = 500,
        num_threads: int = 50,
        num_evolving_threads: int = 10,
        num_conflicting_sets: int = 5,
    ) -> List[Dict]:
        """Generate complete dataset with various scenarios."""
        posts = []

        # Regular posts
        for _ in range(num_posts):
            user = random.choice(self.users)
            topic = random.choice(self.topics)
            is_sarcastic = random.random() < 0.05  # 5% sarcastic
            post = self.generate_post(user, topic, is_sarcastic=is_sarcastic)
            posts.append(post)

        # Regular threads
        for _ in range(num_threads):
            user = random.choice(self.users)
            topic = random.choice(self.topics)
            thread_posts = self.generate_thread(
                user, topic, num_posts=random.randint(3, 8)
            )
            posts.extend(thread_posts)

        # Evolving threads
        for _ in range(num_evolving_threads):
            user = random.choice(self.users)
            topic = random.choice(self.topics)
            evolving_posts = self.generate_evolving_thread(
                user, topic, num_posts=random.randint(4, 7)
            )
            posts.extend(evolving_posts)

        # Conflicting information sets
        for _ in range(num_conflicting_sets):
            topic_pair = random.choice(self.conflicting_info_topics)
            conflicting_posts = self.generate_conflicting_posts(
                topic_pair, num_pairs=random.randint(2, 4)
            )
            posts.extend(conflicting_posts)

        # Sort by timestamp
        posts.sort(key=lambda x: x["timestamp"])

        return posts

    def save_dataset(self, posts: List[Dict], output_path: Path) -> None:
        """Save dataset to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        dataset = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_posts": len(posts),
                "total_users": len(self.users),
                "topics": self.topics,
            },
            "posts": posts,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        print(f"Dataset saved to {output_path}")
        print(f"Total posts: {len(posts)}")
        print(f"Total users: {len(self.users)}")


def generate_mock_data(output_path: Path = Path("data/mock_x_data.json")) -> None:
    """Generate mock X data and save to file."""
    generator = XDataGenerator(seed=42)
    posts = generator.generate_dataset(
        num_posts=1000,
        num_threads=50,
        num_evolving_threads=10,
        num_conflicting_sets=5,
    )
    generator.save_dataset(posts, output_path)


if __name__ == "__main__":
    generate_mock_data()
