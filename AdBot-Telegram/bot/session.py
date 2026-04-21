"""
bot/session.py — In-memory session with TTL, rate limiting, and PRO tier tracking.
"""
import time
from threading import Lock
from datetime import date
from typing import List

from config import (
    State, SESSION_TTL_SECONDS,
    FREE_ADS_PER_DAY, FREE_IMAGES_PER_DAY,
    PRO_ADS_PER_DAY, PRO_IMAGES_PER_DAY,
)


class UserSession:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.state: str = State.IDLE

        # Onboarding
        self.business_type: str = ""
        self.platform: str = ""

        # Product
        self.product_name: str = ""
        self.product_details: str = ""
        self.usp: str = ""
        self.audience: str = ""
        self.photos: List[bytes] = []

        # Language (v2 — multilingual)
        self.language_code: str = "en"   # ISO 639-1 code from Telegram

        # Generated content
        self.current_copy: dict = {}
        self.current_image_url: str = ""
        self.feedback_count: int = 0
        self.history: List[dict] = []

        # ── PRO status ────────────────────────────────────────────────────────
        self.is_pro: bool = False
        self.pro_expires: float = 0.0    # unix timestamp

        # ── Rate limiting ─────────────────────────────────────────────────────
        self.ads_today: int = 0
        self.images_today: int = 0
        self.rate_reset_day: int = date.today().toordinal()

        self.last_active: float = time.time()

    # ── PRO helpers ───────────────────────────────────────────────────────────
    def activate_pro(self, days: int):
        now = time.time()
        if self.is_pro and self.pro_expires > now:
            self.pro_expires += days * 86400       # stack on top
        else:
            self.pro_expires = now + days * 86400
        self.is_pro = True

    def check_pro_expiry(self):
        if self.is_pro and time.time() > self.pro_expires:
            self.is_pro = False

    def pro_days_remaining(self) -> int:
        if not self.is_pro:
            return 0
        remaining = (self.pro_expires - time.time()) / 86400
        return max(0, int(remaining))

    # ── Rate limiting ─────────────────────────────────────────────────────────
    def _reset_if_new_day(self):
        today = date.today().toordinal()
        if self.rate_reset_day != today:
            self.ads_today    = 0
            self.images_today = 0
            self.rate_reset_day = today

    def can_generate_ad(self) -> bool:
        self.check_pro_expiry()
        self._reset_if_new_day()
        limit = PRO_ADS_PER_DAY if self.is_pro else FREE_ADS_PER_DAY
        return self.ads_today < limit

    def can_generate_image(self) -> bool:
        self.check_pro_expiry()
        self._reset_if_new_day()
        limit = PRO_IMAGES_PER_DAY if self.is_pro else FREE_IMAGES_PER_DAY
        return self.images_today < limit

    def ads_remaining(self) -> int:
        self._reset_if_new_day()
        limit = PRO_ADS_PER_DAY if self.is_pro else FREE_ADS_PER_DAY
        return max(0, limit - self.ads_today)

    def record_ad(self):
        self._reset_if_new_day()
        self.ads_today += 1

    def record_image(self):
        self._reset_if_new_day()
        self.images_today += 1

    # ── History ───────────────────────────────────────────────────────────────
    def save_to_history(self, pack: dict):
        self.history.insert(0, pack)
        self.history = self.history[:5]

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def touch(self):
        self.last_active = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > SESSION_TTL_SECONDS

    def reset_for_new_ad(self):
        """Keep PRO status + history + language; clear product & generated content."""
        self.state          = State.IDLE
        self.business_type  = ""
        self.platform       = ""
        self.product_name   = ""
        self.product_details = ""
        self.usp            = ""
        self.audience       = ""
        self.photos         = []
        self.current_copy   = {}
        self.current_image_url = ""
        self.feedback_count = 0
        # Note: language_code is intentionally preserved across ads


class SessionManager:
    def __init__(self):
        self._store: dict[int, UserSession] = {}
        self._lock = Lock()

    def get(self, user_id: int) -> UserSession:
        with self._lock:
            self._evict_expired()
            if user_id not in self._store:
                self._store[user_id] = UserSession(user_id)
            s = self._store[user_id]
            s.touch()
            return s

    def _evict_expired(self):
        expired = [uid for uid, s in self._store.items() if s.is_expired()]
        for uid in expired:
            # Don't evict PRO users who still have active subscriptions
            if not self._store[uid].is_pro:
                del self._store[uid]


# Singleton
sessions = SessionManager()
