"""Shared interaction guardrails to prevent repetitive, one-sided behavior."""
from datetime import datetime, timedelta
from typing import Optional

from database import db
from utils.logger import logger


def _latest_action_with_user(action: str, user_id: str = "", username: str = "") -> Optional[dict]:
    query = {"action": action, "success": True}
    if user_id:
        query["target_user_id"] = str(user_id)
    elif username:
        query["target_user"] = username
    else:
        return None
    return db.activity_logs.find_one(query, sort=[("timestamp", -1)])


def can_engage_user(action: str, user_id: str = "", username: str = "", cooldown_hours: int = 72) -> bool:
    """Generic per-user cooldown for likes/retweets/follows/replies."""
    last_action = _latest_action_with_user(action, user_id=user_id, username=username)
    if not last_action:
        return True

    last_ts = last_action.get("timestamp")
    if not isinstance(last_ts, datetime):
        return False

    cooldown_until = last_ts + timedelta(hours=cooldown_hours)
    if datetime.utcnow() < cooldown_until:
        logger.debug(
            f"Skipping @{username or user_id}: {action} cooldown active until {cooldown_until.isoformat()}"
        )
        return False
    return True


def has_user_talked_back(user_id: str, since: datetime) -> bool:
    """Check if user has mentioned/replied to us after our last outbound reply."""
    if not user_id:
        return False

    author_variants = [user_id]
    if str(user_id).isdigit():
        try:
            author_variants.append(int(user_id))
        except Exception:
            pass

    mention = db.mentions.find_one(
        {
            "author_id": {"$in": author_variants},
            "$or": [
                {"created_at": {"$gt": since}},
                {"received_at": {"$gt": since}},
            ],
        }
    )
    return mention is not None


def can_reply_to_user(user_id: str = "", username: str = "") -> bool:
    """
    Do not repeatedly reply to the same account unless they talk back.
    Also enforces a short reply cooldown even after talk-back.
    """
    last_reply = _latest_action_with_user("reply", user_id=user_id, username=username)
    if not last_reply:
        return True

    last_ts = last_reply.get("timestamp")
    if not isinstance(last_ts, datetime):
        return False

    if not has_user_talked_back(user_id, last_ts):
        logger.debug(f"Skipping @{username or user_id}: no talk-back since last reply")
        return False

    # Even with talk-back, avoid immediate repeated replies.
    return can_engage_user("reply", user_id=user_id, username=username, cooldown_hours=24)


def has_recent_any_engagement(user_id: str = "", username: str = "", cooldown_hours: int = 72) -> bool:
    """Check whether we engaged this user recently with any main action type."""
    if not user_id and not username:
        return False

    query = {
        "action": {"$in": ["reply", "like", "retweet", "follow"]},
        "success": True,
    }
    if user_id:
        query["target_user_id"] = str(user_id)
    elif username:
        query["target_user"] = username

    latest = db.activity_logs.find_one(query, sort=[("timestamp", -1)])
    if not latest:
        return False

    last_ts = latest.get("timestamp")
    if not isinstance(last_ts, datetime):
        return False
    return datetime.utcnow() < (last_ts + timedelta(hours=cooldown_hours))
