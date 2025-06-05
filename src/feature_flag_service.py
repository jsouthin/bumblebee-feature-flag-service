from abc import ABC, abstractmethod
import sqlite3
from typing import Optional, List, Dict, Union


class FeatureFlagStore(ABC):
    @abstractmethod
    def add_customer(self, customer_id: int): pass

    @abstractmethod
    def add_feature(self, feature_name: str, default_enabled: bool = True): pass

    @abstractmethod
    def set_global_flag(self, feature_name: str, is_enabled: bool): pass

    @abstractmethod
    def remove_feature(self, feature_name: str): pass

    @abstractmethod
    def rename_feature(self, old_name: str, new_name: str): pass

    @abstractmethod
    def set_flag(self, feature_name: str, customer_id: Optional[int], user_id: Optional[int], is_enabled: bool): pass

    @abstractmethod
    def remove_customer(self, customer_id: int): pass

    @abstractmethod
    def remove_user(self, user_id: int): pass

    @abstractmethod
    def list_customers_with_feature(self, feature_name: str) -> List[int]: pass

    @abstractmethod
    def list_customers_with_feature_explicitly_enabled(self, feature_name: str) -> List[int]: pass

    @abstractmethod
    def list_customers_with_feature_explicitly_disabled(self, feature_name: str) -> List[int]: pass

    @abstractmethod
    def list_features_for_customer(self, customer_id: int) -> List[str]: pass

    @abstractmethod
    def list_all_features(self) -> List[str]: pass

    @abstractmethod
    def describe_all_features(self) -> List[Dict[str, Union[str, bool, List[int]]]]: pass

    @abstractmethod
    def list_all_customers(self) -> List[int]: pass

    @abstractmethod
    def close(self): pass


class SQLiteFeatureFlagStore(FeatureFlagStore):
    def __init__(self, db_path: str = "feature_flags.db"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INTEGER PRIMARY KEY
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS global_feature_flags (
                    feature_name TEXT PRIMARY KEY,
                    is_enabled BOOLEAN NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS feature_flags (
                    feature_name TEXT NOT NULL,
                    customer_id INTEGER,
                    user_id INTEGER,
                    is_enabled BOOLEAN NOT NULL,
                    PRIMARY KEY (feature_name, customer_id, user_id)
                )
            """)

    def add_customer(self, customer_id: int):
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO customers (customer_id) VALUES (?)", (customer_id,))

    def add_feature(self, feature_name: str, default_enabled: bool = True):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO global_feature_flags (feature_name, is_enabled) VALUES (?, ?)", (feature_name, default_enabled))

    def set_global_flag(self, feature_name: str, is_enabled: bool):
        with self.conn:
            self.conn.execute("""
                INSERT INTO global_feature_flags (feature_name, is_enabled)
                VALUES (?, ?)
                ON CONFLICT(feature_name) DO UPDATE SET is_enabled = excluded.is_enabled
            """, (feature_name, is_enabled))

    def remove_feature(self, feature_name: str):
        with self.conn:
            self.conn.execute("DELETE FROM feature_flags WHERE feature_name = ?", (feature_name,))
            self.conn.execute("DELETE FROM global_feature_flags WHERE feature_name = ?", (feature_name,))

    def rename_feature(self, old_name: str, new_name: str):
        with self.conn:
            self.conn.execute("UPDATE feature_flags SET feature_name = ? WHERE feature_name = ?", (new_name, old_name))
            self.conn.execute("UPDATE global_feature_flags SET feature_name = ? WHERE feature_name = ?", (new_name, old_name))

    def set_flag(self, feature_name: str, customer_id: Optional[int], user_id: Optional[int], is_enabled: bool):
        if customer_id is None and user_id is None:
            raise ValueError("Use add_feature() or set_global_flag() to set global feature flags.")
        with self.conn:
            self.conn.execute("""
                INSERT INTO feature_flags (feature_name, customer_id, user_id, is_enabled)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(feature_name, customer_id, user_id) DO UPDATE SET is_enabled = excluded.is_enabled
            """, (feature_name, customer_id, user_id, is_enabled))

    def remove_customer(self, customer_id: int):
        with self.conn:
            self.conn.execute("DELETE FROM feature_flags WHERE customer_id = ?", (customer_id,))
            self.conn.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))

    def remove_user(self, user_id: int):
        with self.conn:
            self.conn.execute("DELETE FROM feature_flags WHERE user_id = ?", (user_id,))

    def list_customers_with_feature(self, feature_name: str) -> List[int]:
        cursor = self.conn.execute("SELECT is_enabled FROM global_feature_flags WHERE feature_name = ?", (feature_name,))
        row = cursor.fetchone()
        if row and row[0]:
            cursor = self.conn.execute("""
                SELECT customer_id FROM customers
                WHERE customer_id NOT IN (
                    SELECT customer_id FROM feature_flags
                    WHERE feature_name = ? AND is_enabled = 0 AND customer_id IS NOT NULL
                )
            """, (feature_name,))
        else:
            cursor = self.conn.execute("""
                SELECT DISTINCT customer_id FROM feature_flags
                WHERE feature_name = ? AND is_enabled = 1 AND customer_id IS NOT NULL
            """, (feature_name,))
        return [row[0] for row in cursor.fetchall()]

    def list_customers_with_feature_explicitly_enabled(self, feature_name: str) -> List[int]:
        cursor = self.conn.execute("""
            SELECT DISTINCT customer_id FROM feature_flags
            WHERE feature_name = ? AND is_enabled = 1 AND customer_id IS NOT NULL
        """, (feature_name,))
        return [row[0] for row in cursor.fetchall()]

    def list_customers_with_feature_explicitly_disabled(self, feature_name: str) -> List[int]:
        cursor = self.conn.execute("""
            SELECT DISTINCT customer_id FROM feature_flags
            WHERE feature_name = ? AND is_enabled = 0 AND customer_id IS NOT NULL
        """, (feature_name,))
        return [row[0] for row in cursor.fetchall()]

    def list_features_for_customer(self, customer_id: int) -> List[str]:
        cursor = self.conn.execute("SELECT feature_name FROM global_feature_flags WHERE is_enabled = 1")
        global_features = {row[0] for row in cursor.fetchall()}

        cursor = self.conn.execute("""
            SELECT feature_name FROM feature_flags
            WHERE customer_id = ? AND is_enabled = 1
        """, (customer_id,))
        customer_features = {row[0] for row in cursor.fetchall()}

        cursor = self.conn.execute("""
            SELECT feature_name FROM feature_flags
            WHERE customer_id = ? AND is_enabled = 0
        """, (customer_id,))
        blacklisted_features = {row[0] for row in cursor.fetchall()}

        return list((global_features | customer_features) - blacklisted_features)

    def list_all_features(self) -> List[str]:
        cursor = self.conn.execute("SELECT feature_name FROM global_feature_flags")
        return [row[0] for row in cursor.fetchall()]

    def describe_all_features(self) -> List[Dict[str, Union[str, bool, List[int]]]]:
        cursor = self.conn.execute("SELECT feature_name, is_enabled FROM global_feature_flags")
        features = []
        for name, is_enabled in cursor.fetchall():
            features.append({
                "feature_name": name,
                "global_enabled": bool(is_enabled),
                "explicitly_enabled_customers": self.list_customers_with_feature_explicitly_enabled(name),
                "explicitly_disabled_customers": self.list_customers_with_feature_explicitly_disabled(name),
            })
        return features

    def list_all_customers(self) -> List[int]:
        cursor = self.conn.execute("SELECT customer_id FROM customers")
        return [row[0] for row in cursor.fetchall()]

    def close(self):
        self.conn.close()


class FeatureFlagService:
    def __init__(self, store: FeatureFlagStore):
        self.store = store

    def __getattr__(self, item):
        return getattr(self.store, item)
