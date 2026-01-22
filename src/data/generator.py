"""Generate realistic mock X (Twitter) dataset with ambiguity scenarios."""

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.agents.grok_client import GrokClient, GrokAPIError

logger = logging.getLogger(__name__)


class XDataGenerator:
    """Generate mock X (Twitter) data with realistic features."""

    def __init__(
        self,
        seed: int = 42,
        grok_client: Optional[GrokClient] = None,
        use_grok: bool = True,
        grok_temperature: float = 0.8,
        batch_size: int = 5,
    ):
        """
        Initialize generator with random seed and optional Grok integration.

        Args:
            seed: Random seed for reproducibility
            grok_client: Optional GrokClient instance. If None and use_grok=True, will try to create one.
            use_grok: Whether to use Grok for content generation (falls back to templates if False or fails)
            grok_temperature: Temperature for Grok generation (0.0-1.0)
            batch_size: Number of posts to generate per Grok API call
        """
        random.seed(seed)
        np.random.seed(seed)

        self.use_grok = use_grok
        self.grok_temperature = grok_temperature
        self.batch_size = batch_size

        # Initialize Grok client if requested
        if use_grok:
            try:
                self.grok_client = grok_client or GrokClient()
                logger.info("Grok client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Grok client: {e}. Falling back to templates.")
                self.grok_client = None
                self.use_grok = False
        else:
            self.grok_client = None

        # Cache for generated content
        self._content_cache: Dict[str, List[str]] = {}
        self._user_cache: List[Dict] = []

        # Topics and keywords for generating content
        self.topics = [
            "AI", "machine learning", "Python", "JavaScript", "web development",
            "data science", "cloud computing", "cybersecurity", "blockchain",
            "startup", "venture capital", "productivity", "remote work",
        ]

        # User personas for more realistic profiles
        self.user_personas = [
            "tech influencer", "software engineer", "data scientist", "startup founder",
            "product manager", "designer", "tech journalist", "researcher",
            "developer advocate", "entrepreneur", "investor", "consultant",
            "student", "hobbyist", "tech enthusiast",
        ]

        # Ambiguity scenarios templates (fallback)
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

        # Initialize users
        self.users = self._generate_users()

    def _generate_users(self, num_users: int = 50) -> List[Dict]:
        """Generate realistic user profiles, using Grok if available."""
        if self.use_grok and self.grok_client and len(self._user_cache) == 0:
            try:
                return self._generate_users_with_grok(num_users)
            except Exception as e:
                logger.warning(f"Failed to generate users with Grok: {e}. Using template users.")
                return self._generate_template_users(num_users)
        elif len(self._user_cache) > 0:
            return self._user_cache[:num_users]
        else:
            return self._generate_template_users(num_users)

    def _generate_users_with_grok(self, num_users: int) -> List[Dict]:
        """Generate users using Grok LLM."""
        users = []
        batch_size = min(self.batch_size, num_users)

        for batch_start in range(0, num_users, batch_size):
            batch_end = min(batch_start + batch_size, num_users)
            batch_count = batch_end - batch_start

            prompt = f"""Generate {batch_count} realistic X (Twitter) user profiles for tech/startup community.
For each user, provide:
- A realistic username (no spaces, can include underscores/numbers)
- A display name
- A short bio (1-2 sentences)
- User type/persona (from: {', '.join(self.user_personas)})
- Approximate follower count range (small: 100-1K, medium: 1K-50K, large: 50K-500K, influencer: 500K+)

Format as JSON array with fields: username, display_name, bio, persona, follower_range
Example format:
[
  {{"username": "techdev_alex", "display_name": "Alex Chen", "bio": "Building AI tools. Former @Google. Love Python.", "persona": "software engineer", "follower_range": "medium"}},
  {{"username": "startup_insights", "display_name": "Sarah Martinez", "bio": "VC analyst covering early-stage startups. Always learning.", "persona": "investor", "follower_range": "large"}}
]"""

            try:
                response = self.grok_client.chat(
                    [
                        {
                            "role": "system",
                            "content": "You are generating realistic social media user profiles. Always respond with valid JSON only, no markdown formatting.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                )

                # Parse JSON response
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()

                batch_users = json.loads(response)
                if not isinstance(batch_users, list):
                    batch_users = [batch_users]

                # Convert to our format
                for i, user_data in enumerate(batch_users):
                    follower_ranges = {
                        "small": (100, 1000),
                        "medium": (1000, 50000),
                        "large": (50000, 500000),
                        "influencer": (500000, 5000000),
                    }
                    follower_range = user_data.get("follower_range", "medium").lower()
                    min_followers, max_followers = follower_ranges.get(
                        follower_range, (1000, 50000)
                    )

                    user = {
                        "id": f"user_{batch_start + i}",
                        "username": user_data.get("username", f"user_{batch_start + i}"),
                        "display_name": user_data.get("display_name", ""),
                        "bio": user_data.get("bio", ""),
                        "persona": user_data.get("persona", "tech enthusiast"),
                        "followers": random.randint(min_followers, max_followers),
                        "verified": random.random() < 0.1,  # 10% verified
                    }
                    users.append(user)

            except (json.JSONDecodeError, KeyError, Exception) as e:
                logger.warning(f"Error parsing Grok user response: {e}. Using template users for this batch.")
                # Fallback to template users for this batch
                for i in range(batch_count):
                    users.append(self._create_template_user(batch_start + i))

        self._user_cache = users
        return users

    def _generate_template_users(self, num_users: int) -> List[Dict]:
        """Generate users using templates (fallback)."""
        users = []
        for i in range(num_users):
            users.append(self._create_template_user(i))
        return users

    def _create_template_user(self, index: int) -> Dict:
        """Create a single template user."""
        persona = random.choice(self.user_personas)
        follower_ranges = {
            "small": (100, 1000),
            "medium": (1000, 50000),
            "large": (50000, 500000),
            "influencer": (500000, 5000000),
        }
        # Assign follower range based on persona
        if persona in ["tech influencer", "investor", "tech journalist"]:
            follower_range = random.choice(["large", "influencer"])
        elif persona in ["startup founder", "developer advocate"]:
            follower_range = random.choice(["medium", "large"])
        else:
            follower_range = random.choice(["small", "medium"])

        min_followers, max_followers = follower_ranges.get(follower_range, (1000, 50000))

        return {
            "id": f"user_{index}",
            "username": f"{persona.replace(' ', '_')}_{index}",
            "display_name": f"User {index}",
            "bio": f"{persona.title()} interested in tech",
            "persona": persona,
            "followers": random.randint(min_followers, max_followers),
            "verified": random.random() < 0.1,
        }

    def _generate_content_batch_with_grok(
        self,
        requests: List[Dict[str, any]],
    ) -> List[str]:
        """Generate multiple post contents in a single Grok API call."""
        if not self.grok_client or not self.use_grok or len(requests) == 0:
            return [self._generate_realistic_content(r.get("topic", "tech")) for r in requests]

        try:
            # Build batch prompt
            request_descriptions = []
            for i, req in enumerate(requests):
                topic = req.get("topic", "tech")
                user = req.get("user", {})
                post_type = req.get("post_type", "general")
                thread_context = req.get("thread_context")
                
                context_str = ""
                if thread_context:
                    context_str = f" Previous context: {', '.join(thread_context[-2:])}"
                
                request_descriptions.append(
                    f"{i+1}. Topic: {topic}, User: {user.get('persona', 'tech enthusiast')}, "
                    f"Style: {post_type}{context_str}"
                )

            prompt = f"""Generate {len(requests)} realistic X (Twitter) posts.
For each request below, generate one post under 280 characters. Make them natural and authentic.

Requests:
{chr(10).join(request_descriptions)}

Return as a JSON array of strings, one post per element. No markdown formatting, just the JSON array.
Example: ["First post content here", "Second post content here", ...]"""

            response = self.grok_client.chat(
                [
                    {
                        "role": "system",
                        "content": "You are generating realistic social media posts. Always respond with valid JSON array only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.grok_temperature,
                max_tokens=500,
            )

            # Parse JSON response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            contents = json.loads(response)
            if not isinstance(contents, list):
                contents = [contents]

            # Ensure we have the right number of posts
            while len(contents) < len(requests):
                contents.append(self._generate_realistic_content(requests[len(contents)].get("topic", "tech")))

            # Clean up each content
            cleaned_contents = []
            for content in contents[:len(requests)]:
                content = str(content).strip().strip('"').strip("'")
                cleaned_contents.append(content)

            # Cache results
            for i, (req, content) in enumerate(zip(requests, cleaned_contents)):
                cache_key = f"{req.get('topic', 'tech')}_{req.get('user', {}).get('persona', 'general')}_{req.get('post_type', 'general')}"
                if cache_key not in self._content_cache:
                    self._content_cache[cache_key] = []
                self._content_cache[cache_key].append(content)

            return cleaned_contents

        except (GrokAPIError, json.JSONDecodeError, Exception) as e:
            logger.warning(f"Grok batch generation failed: {e}, using templates")
            return [self._generate_realistic_content(r.get("topic", "tech")) for r in requests]

    def _generate_content_with_grok(
        self,
        topic: str,
        user: Dict,
        post_type: str = "general",
        thread_context: Optional[List[str]] = None,
    ) -> str:
        """Generate post content using Grok LLM."""
        if not self.grok_client or not self.use_grok:
            return self._generate_realistic_content(topic)

        # Check cache first
        cache_key = f"{topic}_{user.get('persona', 'general')}_{post_type}"
        if cache_key in self._content_cache:
            cached = self._content_cache[cache_key]
            if cached:
                return random.choice(cached)

        try:
            context_str = ""
            if thread_context:
                context_str = f"\nPrevious thread posts:\n" + "\n".join(
                    f"- {post}" for post in thread_context[-3:]
                )  # Last 3 posts for context

            prompt = f"""Generate a realistic X (Twitter) post about {topic}.
User type: {user.get('persona', 'tech enthusiast')}
Post style: {post_type}
{context_str}
Keep it under 280 characters. Make it sound natural and authentic. Include hashtags and mentions if appropriate. Do not include any prefixes like "Post:" or quotes."""

            content = self.grok_client.chat(
                [
                    {
                        "role": "system",
                        "content": "You are generating realistic social media posts. Respond with only the post content, no explanations or formatting.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.grok_temperature,
                max_tokens=150,
            )

            content = content.strip()
            # Remove quotes if present
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            if content.startswith("'") and content.endswith("'"):
                content = content[1:-1]

            # Cache the result
            if cache_key not in self._content_cache:
                self._content_cache[cache_key] = []
            self._content_cache[cache_key].append(content)

            return content

        except (GrokAPIError, Exception) as e:
            logger.warning(f"Grok generation failed: {e}, using template")
            return self._generate_realistic_content(topic)

    def _generate_realistic_content(self, topic: str) -> str:
        """Generate realistic post content about a topic (fallback templates)."""
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

    def _calculate_engagement_metrics(
        self, user: Dict, content: str, post_type: str = "general"
    ) -> Dict[str, int]:
        """Calculate realistic engagement metrics based on user influence and content."""
        followers = user.get("followers", 1000)
        is_verified = user.get("verified", False)

        # Base engagement rate (percentage of followers who engage)
        base_engagement_rate = 0.01  # 1% base engagement

        # Adjustments based on user type
        if followers > 500000:
            base_engagement_rate *= 0.5  # Large accounts have lower engagement rates
        elif followers < 1000:
            base_engagement_rate *= 2  # Small accounts have higher engagement rates

        if is_verified:
            base_engagement_rate *= 1.5

        # Post type multipliers
        type_multipliers = {
            "hot_take": 3.0,
            "question": 1.5,
            "announcement": 2.0,
            "thread": 1.8,
            "sarcastic": 2.5,
            "general": 1.0,
        }
        multiplier = type_multipliers.get(post_type, 1.0)

        # Content quality heuristic (length, hashtags, mentions)
        content_quality = 1.0
        if "#" in content:
            content_quality *= 1.2
        if "@" in content:
            content_quality *= 1.1
        if len(content) > 200:
            content_quality *= 1.1

        # Calculate metrics with some randomness
        expected_likes = int(followers * base_engagement_rate * multiplier * content_quality)
        expected_retweets = int(expected_likes * 0.1)  # ~10% of likes
        expected_replies = int(expected_likes * 0.05)  # ~5% of likes

        # Add realistic variance (power law distribution for viral posts)
        if random.random() < 0.01:  # 1% chance of going viral
            viral_multiplier = random.uniform(5, 50)
            expected_likes = int(expected_likes * viral_multiplier)
            expected_retweets = int(expected_retweets * viral_multiplier)
            expected_replies = int(expected_replies * viral_multiplier)

        # Add some noise
        likes = max(0, int(np.random.normal(expected_likes, expected_likes * 0.3)))
        retweets = max(0, int(np.random.normal(expected_retweets, expected_retweets * 0.3)))
        replies = max(0, int(np.random.normal(expected_replies, expected_replies * 0.3)))

        return {
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
        }

    def _generate_realistic_timestamp(self, days_ago: int = None) -> datetime:
        """Generate realistic timestamp with activity patterns."""
        if days_ago is None:
            days_ago = random.randint(0, 30)

        base_time = datetime.now() - timedelta(days=days_ago)

        # More activity during business hours (9 AM - 9 PM)
        hour = random.choices(
            range(24),
            weights=[
                0.3, 0.3, 0.2, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 0.9, 0.9, 0.8,
                0.7, 0.8, 0.9, 0.9, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3,
            ],
        )[0]

        timestamp = base_time.replace(
            hour=hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )

        return timestamp

    def generate_post(
        self,
        user: Dict,
        topic: str,
        is_sarcastic: bool = False,
        is_thread: bool = False,
        thread_id: Optional[str] = None,
        post_type: str = "general",
        thread_context: Optional[List[str]] = None,
    ) -> Dict:
        """Generate a single post."""
        timestamp = self._generate_realistic_timestamp()

        if is_sarcastic:
            if self.use_grok and self.grok_client:
                content = self._generate_content_with_grok(
                    topic, user, post_type="sarcastic", thread_context=thread_context
                )
            else:
                content = random.choice(self.sarcasm_templates).format(topic=topic)
            post_type = "sarcastic"
        else:
            content = self._generate_content_with_grok(
                topic, user, post_type=post_type, thread_context=thread_context
            )

        # Calculate realistic engagement
        engagement = self._calculate_engagement_metrics(user, content, post_type)

        post = {
            "id": f"post_{random.randint(10000, 99999)}",
            "user_id": user["id"],
            "username": user["username"],
            "content": content,
            "timestamp": timestamp.isoformat(),
            "likes": engagement["likes"],
            "retweets": engagement["retweets"],
            "replies": engagement["replies"],
            "is_thread": is_thread,
            "thread_id": thread_id,
            "is_sarcastic": is_sarcastic,
            "topic": topic,
        }

        return post

    def generate_thread(
        self,
        user: Dict,
        topic: str,
        num_posts: int = 3,
    ) -> List[Dict]:
        """Generate a thread of connected posts with coherent content."""
        thread_id = f"thread_{random.randint(10000, 99999)}"
        posts = []
        base_time = self._generate_realistic_timestamp()

        # Generate thread posts with context awareness
        thread_context: List[str] = []

        # Initial post
        initial_post = self.generate_post(
            user,
            topic,
            is_thread=True,
            thread_id=thread_id,
            post_type="thread",
            thread_context=None,
        )
        initial_post["timestamp"] = base_time.isoformat()
        posts.append(initial_post)
        thread_context.append(initial_post["content"])

        # Reply posts with context
        for i in range(1, num_posts):
            reply_time = base_time + timedelta(minutes=random.randint(1, 60))
            reply = self.generate_post(
                user,
                topic,
                is_thread=True,
                thread_id=thread_id,
                post_type="thread",
                thread_context=thread_context,
            )
            reply["timestamp"] = reply_time.isoformat()
            posts.append(reply)
            thread_context.append(reply["content"])

        return posts

    def generate_evolving_thread(
        self,
        user: Dict,
        topic: str,
        num_posts: int = 5,
    ) -> List[Dict]:
        """Generate a thread that evolves/changes direction with coherent narrative."""
        thread_id = f"thread_{random.randint(10000, 99999)}"
        posts = []
        base_time = self._generate_realistic_timestamp()

        thread_context: List[str] = []

        # Start with initial perspective
        initial_post = self.generate_post(
            user,
            topic,
            is_thread=True,
            thread_id=thread_id,
            post_type="thread",
            thread_context=None,
        )
        initial_post["timestamp"] = base_time.isoformat()
        posts.append(initial_post)
        thread_context.append(initial_post["content"])

        # Evolve the discussion with context
        evolution_prompts = [
            "Continue the thread by providing an update or reconsideration",
            "Continue the thread by presenting a counterpoint or new perspective",
            "Continue the thread by sharing a new development or insight",
            "Continue the thread by summarizing or concluding the discussion",
        ]

        for i, evolution_prompt in enumerate(evolution_prompts[: num_posts - 1], 1):
            reply_time = base_time + timedelta(hours=random.randint(1, 24))

            if self.use_grok and self.grok_client:
                # Use Grok to generate coherent continuation
                try:
                    prompt = f"""Generate the next post in a thread about {topic}.
Previous posts in thread:
{chr(10).join(f"{j+1}. {post}" for j, post in enumerate(thread_context))}

{evolution_prompt}. Keep it under 280 characters. Make it flow naturally from the previous posts."""
                    content = self.grok_client.chat(
                        [
                            {
                                "role": "system",
                                "content": "You are generating realistic social media thread continuations. Respond with only the post content.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=self.grok_temperature,
                        max_tokens=150,
                    )
                    content = content.strip().strip('"').strip("'")
                except Exception as e:
                    logger.warning(f"Grok thread evolution failed: {e}, using template")
                    content = f"Update {i}: {self._generate_realistic_content(topic)}"
            else:
                content = f"Update {i}: {self._generate_realistic_content(topic)}"

            reply = self.generate_post(
                user,
                topic,
                is_thread=True,
                thread_id=thread_id,
                post_type="thread",
                thread_context=thread_context,
            )
            reply["timestamp"] = reply_time.isoformat()
            reply["content"] = content
            posts.append(reply)
            thread_context.append(content)

        return posts

    def generate_conflicting_posts(
        self,
        topic_pair: tuple,
        num_pairs: int = 3,
    ) -> List[Dict]:
        """Generate posts with conflicting information."""
        posts = []
        base_time = self._generate_realistic_timestamp()

        for i in range(num_pairs):
            user1 = random.choice(self.users)
            user2 = random.choice(self.users)

            # Generate more realistic conflicting posts with Grok if available
            if self.use_grok and self.grok_client:
                try:
                    content1 = self._generate_content_with_grok(
                        topic_pair[0], user1, post_type="hot_take"
                    )
                    content2 = self._generate_content_with_grok(
                        topic_pair[1], user2, post_type="hot_take"
                    )
                except Exception:
                    content1 = topic_pair[0]
                    content2 = topic_pair[1]
            else:
                content1 = topic_pair[0]
                content2 = topic_pair[1]

            # Post supporting first perspective
            post1 = self.generate_post(
                user1, "conflicting_info", post_type="hot_take"
            )
            post1["content"] = content1
            post1["timestamp"] = (base_time + timedelta(hours=i)).isoformat()
            post1["topic"] = "conflicting_info"

            # Post supporting second perspective
            post2 = self.generate_post(
                user2, "conflicting_info", post_type="hot_take"
            )
            post2["content"] = content2
            post2["timestamp"] = (base_time + timedelta(hours=i, minutes=30)).isoformat()
            post2["topic"] = "conflicting_info"

            posts.extend([post1, post2])

        return posts

    def generate_dataset(
        self,
        num_posts: int = 500,
        num_threads: int = 50,
        num_evolving_threads: int = 10,
        num_conflicting_sets: int = 5,
        use_grok: Optional[bool] = None,
        grok_temperature: Optional[float] = None,
    ) -> List[Dict]:
        """
        Generate complete dataset with various scenarios.

        Args:
            num_posts: Number of regular posts to generate
            num_threads: Number of regular threads to generate
            num_evolving_threads: Number of evolving threads to generate
            num_conflicting_sets: Number of conflicting post sets to generate
            use_grok: Override instance use_grok setting
            grok_temperature: Override instance grok_temperature setting
        """
        # Override settings if provided
        original_use_grok = self.use_grok
        original_temperature = self.grok_temperature

        if use_grok is not None:
            self.use_grok = use_grok and (self.grok_client is not None)
        if grok_temperature is not None:
            self.grok_temperature = grok_temperature

        posts = []
        total_items = num_posts + num_threads + num_evolving_threads + num_conflicting_sets

        try:
            # Regular posts with batch processing
            logger.info(f"Generating {num_posts} regular posts...")
            
            if self.use_grok and self.grok_client and num_posts > self.batch_size:
                # Use batch processing for efficiency
                batch_requests = []
                batch_users = []
                batch_topics = []
                batch_is_sarcastic = []
                batch_post_types = []
                
                for i in range(num_posts):
                    user = random.choice(self.users)
                    topic = random.choice(self.topics)
                    is_sarcastic = random.random() < 0.05  # 5% sarcastic
                    post_type = random.choice(["general", "question", "announcement", "hot_take"])
                    
                    batch_requests.append({
                        "topic": topic,
                        "user": user,
                        "post_type": "sarcastic" if is_sarcastic else post_type,
                        "thread_context": None,
                    })
                    batch_users.append(user)
                    batch_topics.append(topic)
                    batch_is_sarcastic.append(is_sarcastic)
                    batch_post_types.append(post_type)
                    
                    # Process batch when full or at end
                    if len(batch_requests) >= self.batch_size or i == num_posts - 1:
                        try:
                            batch_contents = self._generate_content_batch_with_grok(batch_requests)
                        except Exception as e:
                            logger.warning(f"Batch generation failed: {e}, falling back to individual generation")
                            batch_contents = [self._generate_realistic_content(t) for t in batch_topics]
                        
                        # Create posts from batch results
                        for j, content in enumerate(batch_contents):
                            timestamp = self._generate_realistic_timestamp()
                            engagement = self._calculate_engagement_metrics(
                                batch_users[j], content, batch_post_types[j]
                            )
                            post = {
                                "id": f"post_{random.randint(10000, 99999)}",
                                "user_id": batch_users[j]["id"],
                                "username": batch_users[j]["username"],
                                "content": content,
                                "timestamp": timestamp.isoformat(),
                                "likes": engagement["likes"],
                                "retweets": engagement["retweets"],
                                "replies": engagement["replies"],
                                "is_thread": False,
                                "thread_id": None,
                                "is_sarcastic": batch_is_sarcastic[j],
                                "topic": batch_topics[j],
                            }
                            posts.append(post)
                        
                        # Clear batch
                        batch_requests = []
                        batch_users = []
                        batch_topics = []
                        batch_is_sarcastic = []
                        batch_post_types = []
                        
                        if (i + 1) % (self.batch_size * 10) == 0:
                            logger.info(f"Generated {i + 1}/{num_posts} posts...")
            else:
                # Individual generation (fallback or small batches)
                for i in range(num_posts):
                    if (i + 1) % 100 == 0:
                        logger.info(f"Generated {i + 1}/{num_posts} posts...")
                    user = random.choice(self.users)
                    topic = random.choice(self.topics)
                    is_sarcastic = random.random() < 0.05  # 5% sarcastic
                    post_type = random.choice(["general", "question", "announcement", "hot_take"])
                    post = self.generate_post(user, topic, is_sarcastic=is_sarcastic, post_type=post_type)
                    posts.append(post)

            # Regular threads
            logger.info(f"Generating {num_threads} regular threads...")
            for i in range(num_threads):
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated {i + 1}/{num_threads} threads...")
                user = random.choice(self.users)
                topic = random.choice(self.topics)
                thread_posts = self.generate_thread(
                    user, topic, num_posts=random.randint(3, 8)
                )
                posts.extend(thread_posts)

            # Evolving threads
            logger.info(f"Generating {num_evolving_threads} evolving threads...")
            for i in range(num_evolving_threads):
                user = random.choice(self.users)
                topic = random.choice(self.topics)
                evolving_posts = self.generate_evolving_thread(
                    user, topic, num_posts=random.randint(4, 7)
                )
                posts.extend(evolving_posts)

            # Conflicting information sets
            logger.info(f"Generating {num_conflicting_sets} conflicting post sets...")
            for i in range(num_conflicting_sets):
                topic_pair = random.choice(self.conflicting_info_topics)
                conflicting_posts = self.generate_conflicting_posts(
                    topic_pair, num_pairs=random.randint(2, 4)
                )
                posts.extend(conflicting_posts)

        finally:
            # Restore original settings
            self.use_grok = original_use_grok
            self.grok_temperature = original_temperature

        # Sort by timestamp
        posts.sort(key=lambda x: x["timestamp"])

        logger.info(f"Generated {len(posts)} total posts")
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
                "used_grok": self.use_grok and self.grok_client is not None,
            },
            "posts": posts,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        print(f"Dataset saved to {output_path}")
        print(f"Total posts: {len(posts)}")
        print(f"Total users: {len(self.users)}")
        if self.use_grok and self.grok_client:
            print("Generated using Grok LLM")


def generate_mock_data(
    output_path: Path = Path("data/mock_x_data.json"),
    use_grok: bool = True,
    grok_temperature: float = 0.8,
) -> None:
    """
    Generate mock X data and save to file.

    Args:
        output_path: Path to save the generated dataset
        use_grok: Whether to use Grok for generation
        grok_temperature: Temperature for Grok generation
    """
    generator = XDataGenerator(
        seed=42,
        use_grok=use_grok,
        grok_temperature=grok_temperature,
    )
    posts = generator.generate_dataset(
        num_posts=100,
        num_threads=25,
        num_evolving_threads=5,
        num_conflicting_sets=3,
    )
    generator.save_dataset(posts, output_path)


if __name__ == "__main__":
    generate_mock_data()
