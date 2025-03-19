import numpy as np
import random
import tensorflow as tf
from tensorflow import keras
from app.models import ForumViewHistory, ForumThread, RecommendedTopicHistory, ForumReply, UserProfile
from collections import defaultdict
import logging
from datetime import timedelta, datetime
from django.utils import timezone
from django.db import transaction
import matplotlib.pyplot as plt
import io
import base64
from django.core.exceptions import ObjectDoesNotExist
import psutil
from collections import defaultdict

#Log Rewards
logger = logging.getLogger('app') 

class QLearningRecommender:
    def __init__(self, alpha=0.1, gamma=0.99, epsilon=0.05):
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration-exploitation tradeoff
        self.q_table = defaultdict(lambda: np.zeros(10, 5.0))  # 10 actions for simplicity
        
        # Lightweight NN for Q-value approximation (SOL 3)
        self.model = self.build_model()

    def build_model(self):
        model = keras.models.Sequential([
            keras.layers.Input(shape=(5,)),  # 5 Features in State Representation
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(12, activation='linear')  # 10 possible actions (topics)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def get_state(self, user_profile, user_id):
        """
        Create a feature-rich state based on user profile data. (SOL 1)
        """
        engagement_time = sum([
            entry.time_spent 
            for entry in ForumViewHistory.objects.filter(user_id=user_id)
        ])
        
        state = [
            user_profile.age,
            sum(user_profile.category_like_count.values()),
            sum(user_profile.category_dislike_count.values()),
            sum(user_profile.category_comment_count.values()),
            engagement_time
        ]
        return np.array(state, dtype=np.float32)

    def choose_action(self, state):
        """
        Choose an action using epsilon-greedy policy.
        """
        if np.random.rand() < self.epsilon:
            return random.choice(range(10))  # Explore
        else:
            q_values = self.model.predict(np.array([state]), verbose=0)
            return np.argmax(q_values[0])  # Exploit

    def calculate_reward(self, user_profile, user_id, category_name, topic_id):
        """
        Dynamic Reward Calculation. (SOL 2)
        """
        like_score = user_profile.category_like_count.get(category_name, 0)
        dislike_score = user_profile.category_dislike_count.get(category_name, 0)
        comment_score = user_profile.category_comment_count.get(category_name, 0)

        # Engagement time from ForumViewHistory
        engagement_time = sum([
            entry.time_spent
            for entry in ForumViewHistory.objects.filter(user_id=user_id, category__name=category_name)
        ])

        viewed_recommendations = RecommendedTopicHistory.objects.filter(
            user_id=user_id, forum_thread__category__name=category_name, viewed=True
        ).count()

        # Gradually reduce reward for repeat content over time
        decay_factor = 0.9 ** viewed_recommendations  
        # Penalty for repeat recommendations that have been viewed
        penalty = 0

        penalty = np.log1p(viewed_recommendations) * 2  # Slower growth in penalties (gradual as "viewed" become more frequent)
        
        # Logarithm to dampen large values
        normalized_time = np.log1p(engagement_time)

        total_feedback = like_score + comment_score + dislike_score
        #positive vs negative interactions
        satisfaction_ratio = (like_score + comment_score) / total_feedback if total_feedback > 0 else 0.5
        
        # Retrieve topic details for freshness check
        try:
            topic = ForumThread.objects.get(id=topic_id)
            days_old = (timezone.now() - topic.created_at).days
        except ObjectDoesNotExist:
            days_old = 0  # Treat missing topics as 'new' to avoid errors
            topic = None  # Explicitly set `topic` to None

        # New topic booster (longevity)
        if days_old < 30:
            new_topic_boost = 1.5
            is_new_topic = True
        elif days_old < 90:
            new_topic_boost = 1.2
            is_new_topic = False
        elif days_old < 180:
            new_topic_boost = 1.0
            is_new_topic = False
        else:
            new_topic_boost = 0.5
            is_new_topic = False

        reward = (
            (like_score * 2) +
            (comment_score * 1.5) +
            (normalized_time * satisfaction_ratio * 0.3) -
            ((dislike_score * 2) + penalty * (decay_factor * 1.5))
            * new_topic_boost
        )

        # Log topic details if available
        if topic:
            logger.info(f"[TOPIC CHECK] Topic ID: {topic.id} | Created At: {topic.created_at} | "
                        f"Days Old: {days_old} | Is New Topic: {is_new_topic} | "
                        f"New Topic Boost: {new_topic_boost}")
        else:
            logger.info(f"[TOPIC CHECK] Topic ID: {topic_id} (Not Found) | Days Old: {days_old} | "
                        f"Is New Topic: {is_new_topic} | New Topic Boost: {new_topic_boost}")
        logger.info(f"[REWARD CALCULATION] Category: {category_name} | Likes: {like_score} | "
                    f"Dislikes: {dislike_score} | Comments: {comment_score} | "
                    f"Engagement Time: {engagement_time} | Viewed Recommendations: {viewed_recommendations} | "
                    f"Penalty: {penalty} | Final Reward: {reward}")
        
        return reward

    def update_q_value(self, state, action, reward, next_state):
        """
        Q-value update using Bellman Equation.
        """
        q_values = self.model.predict(np.array([state]), verbose=0)
        next_q_values = self.model.predict(np.array([next_state]), verbose=0)

        q_values[0][action] = reward + self.gamma * np.max(next_q_values[0])

        self.model.fit(np.array([state]), q_values, verbose=0)

    def recommend_topics(self, user_profile, user_id):
        state = self.get_state(user_profile, user_id)
        action = self.choose_action(state)

        # Exclude already viewed topics immediately
        viewed_topic_ids = RecommendedTopicHistory.objects.filter(
            user_id=user_id, viewed=True
        ).values_list('forum_thread_id', flat=True)

        # Filter recommended topics excluding previously viewed ones
        recommended_topics = ForumThread.objects.exclude(id__in=viewed_topic_ids)[action:action + 12]

        # Track recommended topics in the new table
        for topic in recommended_topics:
            RecommendedTopicHistory.objects.get_or_create(
                user_id=user_id,
                forum_thread=topic
            )

        return recommended_topics

    # QL Data
    def reset_q_learning_data(self):
        """Resets Q-values, accumulated rewards, memory usage, and database entries."""

        # Reset Q-values, NN weights, and in-memory data
        self.q_table = defaultdict(lambda: np.zeros(10, 5.0))  # Reset Q-table
        self.model.set_weights(self.build_model().get_weights())  # Reset NN weights
        self.reward_data = defaultdict(list)
        self.q_values = {}
        self.memory_usage = {}

        # Database Cleanup: Clear specified tables and reset profile fields
        with transaction.atomic():
            ForumReply.objects.all().delete()

            # Clear likes and dislikes in ForumThread entries
            for thread in ForumThread.objects.all():
                thread.likes.clear()
                thread.dislikes.clear()

            ForumViewHistory.objects.all().delete()
            RecommendedTopicHistory.objects.all().delete()

            # Reset `UserProfile` dictionary fields to empty dicts
            UserProfile.objects.update(
                category_comment_count={},
                category_like_count={},
                category_dislike_count={}
            )

        logger.info("✅ Data successfully flushed: Tables cleared and Q-values reset.")


