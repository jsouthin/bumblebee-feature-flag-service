import sys
sys.path.append("src")
from feature_flag_service import FeatureFlagService, SQLiteFeatureFlagStore
import unittest
import os

class TestFeatureFlagService(unittest.TestCase):

    DB_PATH = "test_feature_flags.db"

    def setUp(self):
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)
        store = SQLiteFeatureFlagStore(db_path=self.DB_PATH)
        self.service = FeatureFlagService(store)
        self.service.add_customer(1)
        self.service.add_customer(2)

    def tearDown(self):
        self.service.close()
        if os.path.exists(self.DB_PATH):
            os.remove(self.DB_PATH)

    def test_add_and_remove_feature(self):
        self.service.add_feature("dashboard")
        self.assertIn("dashboard", self.service.list_features_for_customer(1))
        self.service.remove_feature("dashboard")
        self.assertNotIn("dashboard", self.service.list_features_for_customer(1))

    def test_global_flag_toggle(self):
        self.service.add_feature("auth", default_enabled=False)
        self.assertNotIn(1, self.service.list_customers_with_feature("auth"))
        self.service.set_global_flag("auth", True)
        self.assertIn(1, self.service.list_customers_with_feature("auth"))

    def test_blacklist_override(self):
        self.service.add_feature("inbox")
        self.service.set_flag("inbox", customer_id=2, user_id=None, is_enabled=False)
        customers = self.service.list_customers_with_feature("inbox")
        self.assertIn(1, customers)
        self.assertNotIn(2, customers)

    def test_explicit_enables_and_disables(self):
        self.service.set_flag("export", customer_id=1, user_id=None, is_enabled=True)
        self.service.set_flag("export", customer_id=2, user_id=None, is_enabled=False)
        self.assertIn(1, self.service.list_customers_with_feature_explicitly_enabled("export"))
        self.assertIn(2, self.service.list_customers_with_feature_explicitly_disabled("export"))

    def test_rename_feature(self):
        self.service.add_feature("old_feature")
        self.service.rename_feature("old_feature", "new_feature")
        self.assertIn("new_feature", self.service.list_features_for_customer(1))
        self.assertNotIn("old_feature", self.service.list_features_for_customer(1))

if __name__ == '__main__':
    unittest.main()
