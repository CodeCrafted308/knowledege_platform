from typing import List
from app.models import BadgeType

class BadgeService:
    def __init__(self):
        self.badge_requirements = {
            BadgeType.NEWCOMER: {
                "min_reliability_score": 0,
                "min_posts": 0,
                "description": "Welcome to the platform!"
            },
            BadgeType.RELIABLE_SOURCE: {
                "min_reliability_score": 60,
                "min_posts": 5,
                "description": "Consistently shares reliable content"
            },
            BadgeType.EXPERT_CONTRIBUTOR: {
                "min_reliability_score": 75,
                "min_posts": 15,
                "description": "Expert-level content contributor"
            },
            BadgeType.TRUSTED_AUTHOR: {
                "min_reliability_score": 85,
                "min_posts": 25,
                "description": "Highly trusted content author"
            },
            BadgeType.KNOWLEDGE_MASTER: {
                "min_reliability_score": 95,
                "min_posts": 50,
                "description": "Master of knowledge sharing"
            }
        }
    
    def evaluate_user_badges(self, reliability_score: float, posts_count: int, current_badges: List[BadgeType]) -> List[BadgeType]:
        """Evaluate and return updated badges for a user"""
        new_badges = []
        
        for badge_type, requirements in self.badge_requirements.items():
            if (reliability_score >= requirements["min_reliability_score"] and
                posts_count >= requirements["min_posts"]):
                new_badges.append(badge_type)
        
        # Sort badges by priority (highest first)
        badge_priority = {
            BadgeType.KNOWLEDGE_MASTER: 5,
            BadgeType.TRUSTED_AUTHOR: 4,
            BadgeType.EXPERT_CONTRIBUTOR: 3,
            BadgeType.RELIABLE_SOURCE: 2,
            BadgeType.NEWCOMER: 1
        }
        
        new_badges.sort(key=lambda x: badge_priority.get(x, 0), reverse=True)
        
        return new_badges
    
    def get_badge_info(self, badge_type: BadgeType) -> dict:
        """Get information about a specific badge"""
        return self.badge_requirements.get(badge_type, {
            "min_reliability_score": 0,
            "min_posts": 0,
            "description": "Badge information not available"
        })
    
    def get_all_badges_info(self) -> dict:
        """Get information about all badges"""
        return {
            badge_type.value: requirements
            for badge_type, requirements in self.badge_requirements.items()
        }
    
    def get_next_badge_progress(self, reliability_score: float, posts_count: int) -> dict:
        """Get progress towards the next badge"""
        current_badges = self.evaluate_user_badges(reliability_score, posts_count, [])
        
        # Find the highest current badge
        badge_priority = {
            BadgeType.KNOWLEDGE_MASTER: 5,
            BadgeType.TRUSTED_AUTHOR: 4,
            BadgeType.EXPERT_CONTRIBUTOR: 3,
            BadgeType.RELIABLE_SOURCE: 2,
            BadgeType.NEWCOMER: 1
        }
        
        highest_current_priority = 0
        for badge in current_badges:
            highest_current_priority = max(highest_current_priority, badge_priority.get(badge, 0))
        
        # Find the next badge
        next_badge = None
        for badge_type in sorted(self.badge_requirements.keys(), 
                                key=lambda x: badge_priority.get(x, 0), reverse=True):
            if badge_priority.get(badge_type, 0) > highest_current_priority:
                next_badge = badge_type
                break
        
        if not next_badge:
            return {
                "next_badge": None,
                "message": "You've achieved the highest badge!",
                "progress": 100
            }
        
        requirements = self.badge_requirements[next_badge]
        
        # Calculate progress
        reliability_progress = min(100, (reliability_score / requirements["min_reliability_score"]) * 100)
        posts_progress = min(100, (posts_count / requirements["min_posts"]) * 100) if requirements["min_posts"] > 0 else 100
        
        overall_progress = (reliability_progress + posts_progress) / 2
        
        return {
            "next_badge": next_badge.value,
            "requirements": requirements,
            "progress": overall_progress,
            "reliability_progress": reliability_progress,
            "posts_progress": posts_progress,
            "message": f"Progress towards {next_badge.value.replace('_', ' ').title()}"
        }
