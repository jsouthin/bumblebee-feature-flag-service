# Feature Flag Service

A lightweight feature flag management service using SQLite, designed to support feature toggling at both the `customer_id` and `user_id` levels. This implementation is suitable for MVPs and can scale to more robust backends (e.g., PostgreSQL on RDS) later.

## Features

- Add/remove features
- Rename features
- Add/remove customers
- Add/remove users
- Enable/disable features globally
- Enable/disable features per customer/user
- List all customers with a feature enabled
- List all enabled features for a customer
- List only customers with a feature explicitly enabled
- List only customers with a feature explicitly disabled

## Getting Started

### Prerequisites
- Python 3.7+
- No external dependencies required

### Running the Script (Programmatically)
```bash
python feature_flag_service.py
```

### Running via CLI
Use the `cli.py` script for command-line access.

#### Examples
```bash
python cli.py add-feature dashboard --default-enabled
python cli.py add-customer 101
python cli.py set-flag dashboard --customer-id 101 --enabled
python cli.py list-features 101
python cli.py list-customers dashboard
python cli.py list-customers-enabled dashboard
python cli.py list-customers-disabled dashboard
```

### Database
All data is persisted in a local SQLite database file named `feature_flags.db`. You can delete this file to reset all data.

## API Overview

### Initialization
```python
service = FeatureFlagService()
```

### Feature Management
```python
service.add_feature("feature_name", default_enabled=True)       # Add feature (globally enabled or disabled)
service.set_global_flag("feature_name", is_enabled=False)        # Update global flag
service.rename_feature("old_name", "new_name")                   # Rename feature
service.remove_feature("feature_name")                           # Remove feature completely
```

### Customer/User Management
```python
service.add_customer(123)
service.remove_customer(123)
service.remove_user(456)
```

### Feature Flags
```python
service.set_flag("feature", customer_id=123, user_id=None, is_enabled=True)  # Enable for customer
service.set_flag("feature", customer_id=None, user_id=456, is_enabled=False)  # Disable for user
```

### Queries
```python
service.list_customers_with_feature("feature")                  # List customer_ids with feature enabled
service.list_features_for_customer(123)                          # List features enabled for customer
service.list_customers_with_feature_explicitly_enabled("feature")  # Only customers with feature explicitly enabled
service.list_customers_with_feature_explicitly_disabled("feature") # Only customers with feature explicitly disabled
```

### Cleanup
```python
service.close()
```

## Notes
- Global flags apply to all customers unless explicitly disabled (blacklisted).
- Conflicts are resolved by prioritizing specific overrides over global settings.
- Use `add_feature` or `set_global_flag` to set defaults.
- Modifications are persisted even after script termination.

## CLI vs Programmatic Use
- **CLI** is great for ops/debugging/scripts and simple integrations (e.g., shell automation, deployment toggles).
- **Python API** is better for embedding in your application logic or writing tests.

## Future Enhancements
- REST API wrapper (e.g., FastAPI)
- CLI interface
- Percentage rollouts or cohort-based toggles
- Admin dashboard for visualization

---

MIT License
