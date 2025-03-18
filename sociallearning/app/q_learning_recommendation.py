import numpy as np
import random
import tensorflow as tf
from tensorflow import keras
from app.models import ForumViewHistory, ForumThread, RecommendedTopicHistory
from collections import defaultdict
import logging
from datetime import timedelta
from django.utils import timezone

#Log Rewards
logger = logging.getLogger(__name__)

class QLearningRecommender:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.9):
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration-exploitation tradeoff
        self.q_table = defaultdict(lambda: np.zeros(10))  # 10 actions for simplicity
        
        # Lightweight NN for Q-value approximation
        self.model = self.build_model()

    def build_model(self):
        model = keras.models.Sequential([
            keras.layers.Input(shape=(5,)),  # 5 Features in State Representation
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(10, activation='linear')  # 10 possible actions (topics)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model

    def get_state(self, user_profile, user_id):
        """
        Create a feature-rich state based on user profile data.
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
        Dynamic Reward Calculation.
        """
        like_score = user_profile.category_like_count.get(category_name, 0)
        dislike_score = user_profile.category_dislike_count.get(category_name, 0)
        comment_score = user_profile.category_comment_count.get(category_name, 0)

        # Engagement time from ForumViewHistory
        engagement_time = sum([
            entry.time_spent
            for entry in ForumViewHistory.objects.filter(user_id=user_id, category__name=category_name)
        ])

        # Penalty for repeat recommendations that have been viewed
        penalty = 0
        viewed_recommendations = RecommendedTopicHistory.objects.filter(
            user_id=user_id, forum_thread__category__name=category_name, viewed=True
        ).count()

        if viewed_recommendations > 0:
            penalty = viewed_recommendations * 2  # Penalty value (adjust as needed)

        # Dynamic Reward Calculation
        reward = (
            (like_score * 2) -
            (dislike_score * 1.5) +
            (comment_score * 1.2) +
            (engagement_time * 0.5) -
            penalty  # Deduct penalty for repeat viewed recommendations
        )

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
        recommended_topics = ForumThread.objects.exclude(id__in=viewed_topic_ids)[action:action + 8]

        # Track recommended topics in the new table
        for topic in recommended_topics:
            RecommendedTopicHistory.objects.get_or_create(
                user_id=user_id,
                forum_thread=topic
            )

        return recommended_topics
