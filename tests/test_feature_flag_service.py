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

    def test_user_level_feature_flags(self):
        self.service.add_feature("user_feature")
        self.service.set_flag("user_feature", customer_id=1, user_id=100, is_enabled=True)
        self.service.set_flag("user_feature", customer_id=1, user_id=101, is_enabled=False)
        self.assertIn(1, self.service.list_customers_with_feature("user_feature"))
        self.service.remove_user(100)
        self.assertIn(1, self.service.list_customers_with_feature("user_feature"))

    def test_list_all_features(self):
        self.service.add_feature("feature1")
        self.service.add_feature("feature2")
        features = self.service.list_all_features()
        self.assertIn("feature1", features)
        self.assertIn("feature2", features)

    def test_list_all_customers(self):
        customers = self.service.list_all_customers()
        self.assertIn(1, customers)
        self.assertIn(2, customers)
        self.service.remove_customer(1)
        customers = self.service.list_all_customers()
        self.assertNotIn(1, customers)
        self.assertIn(2, customers)

    def test_describe_all_features(self):
        self.service.add_feature("feature1", default_enabled=True)
        self.service.add_feature("feature2", default_enabled=False)
        self.service.set_flag("feature2", customer_id=1, user_id=None, is_enabled=True)
        
        descriptions = self.service.describe_all_features()
        feature1_desc = next(d for d in descriptions if d["feature_name"] == "feature1")
        feature2_desc = next(d for d in descriptions if d["feature_name"] == "feature2")
        
        self.assertTrue(feature1_desc["global_enabled"])
        self.assertFalse(feature2_desc["global_enabled"])
        self.assertIn(1, feature2_desc["explicitly_enabled_customers"])

    def test_invalid_flag_setting(self):
        with self.assertRaises(ValueError):
            self.service.set_flag("feature", customer_id=None, user_id=None, is_enabled=True)

    def test_feature_default_state(self):
        self.service.add_feature("enabled_feature", default_enabled=True)
        self.service.add_feature("disabled_feature", default_enabled=False)
        
        self.assertIn(1, self.service.list_customers_with_feature("enabled_feature"))
        self.assertNotIn(1, self.service.list_customers_with_feature("disabled_feature"))

if __name__ == '__main__':
    unittest.main()
