"""
bot/session.py — In-memory session manager with TTL + per-user rate limiting.

No external dependency needed. If you later switch to Upstash Redis, only
this file needs changing — all handler code stays the same.
"""
import time
from threading import Lock
from config import SESSION_TTL_SECONDS, MAX_ADS_PER_DAY, MAX_IMAGES_PER_DAY, State


class UserSession:
    """Holds the full conversation state for one user."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.state: str = State.IDLE

        # Onboarding choices
        self.business_type: str = ""       # food / fashion / tech / services / other
        self.platform: str = ""            # instagram / whatsapp / google / poster / all

        # Product info
        self.product_name: str = ""
        self.product_details: str = ""
        self.usp: str = ""
        self.audience: str = ""
        self.photos: list[bytes] = []      # raw bytes of uploaded photos

        # Generated content
        self.current_copy: dict = {}       # {headline, body, cta, hashtags, audience_desc, ab_variation}
        self.current_image_url: str = ""
        self.feedback_count: int = 0       # how many times user regenerated copy
        self.history: list[dict] = []      # last 5 delivered ad packs

        # Timing
        self.last_active: float = time.time()

        # Rate limiting (resets daily)
        self.ads_today: int = 0
        self.images_today: int = 0
        self.rate_reset_day: int = _today()

    def touch(self):
        self.last_active = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > SESSION_TTL_SECONDS

    def _reset_rate_if_new_day(self):
        today = _today()
        if self.rate_reset_day != today:
            self.ads_today = 0
            self.images_today = 0
            self.rate_reset_day = today

    def can_generate_ad(self) -> bool:
        self._reset_rate_if_new_day()
        return self.ads_today < MAX_ADS_PER_DAY

    def can_generate_image(self) -> bool:
        self._reset_rate_if_new_day()
        return self.images_today < MAX_IMAGES_PER_DAY

    def record_ad(self):
        self._reset_rate_if_new_day()
        self.ads_today += 1

    def record_image(self):
        self._reset_rate_if_new_day()
        self.images_today += 1

    def save_to_history(self, pack: dict):
        self.history.insert(0, pack)
        self.history = self.history[:5]        # keep last 5 only

    def reset_for_new_ad(self):
        """Clear product & generated content, keep settings & history."""
        self.state = State.IDLE
        self.business_type = ""
        self.platform = ""
        self.product_name = ""
        self.product_details = ""
        self.usp = ""
        self.audience = ""
        self.photos = []
        self.current_copy = {}
        self.current_image_url = ""
        self.feedback_count = 0


def _today() -> int:
    from datetime import date
    return date.today().toordinal()


class SessionManager:
    """Thread-safe global session store."""

    def __init__(self):
        self._store: dict[int, UserSession] = {}
        self._lock = Lock()

    def get(self, user_id: int) -> UserSession:
        with self._lock:
            self._evict_expired()
            if user_id not in self._store:
                self._store[user_id] = UserSession(user_id)
            session = self._store[user_id]
            session.touch()
            return session

    def delete(self, user_id: int):
        with self._lock:
            self._store.pop(user_id, None)

    def _evict_expired(self):
        expired = [uid for uid, s in self._store.items() if s.is_expired()]
        for uid in expired:
            del self._store[uid]

    def all_user_ids(self) -> list[int]:
        with self._lock:
            return list(self._store.keys())


# Singleton — import and use everywhere
sessions = SessionManager()
