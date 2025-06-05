import argparse
from feature_flag_service import FeatureFlagService, SQLiteFeatureFlagStore

def main():
    parser = argparse.ArgumentParser(description="Feature Flag Service CLI")
    parser.add_argument("--db-path", default="feature_flags.db", help="Path to the SQLite database file")
    subparsers = parser.add_subparsers(dest="command")

    # Add feature
    p = subparsers.add_parser("add-feature")
    p.add_argument("name")
    p.add_argument("--default-enabled", action="store_true")

    # Remove feature
    p = subparsers.add_parser("remove-feature")
    p.add_argument("name")

    # Rename feature
    p = subparsers.add_parser("rename-feature")
    p.add_argument("old_name")
    p.add_argument("new_name")

    # Add customer
    p = subparsers.add_parser("add-customer")
    p.add_argument("customer_id", type=int)

    # Remove customer
    p = subparsers.add_parser("remove-customer")
    p.add_argument("customer_id", type=int)

    # Set flag
    p = subparsers.add_parser("set-flag")
    p.add_argument("feature")
    p.add_argument("--customer-id", type=int)
    p.add_argument("--user-id", type=int)
    p.add_argument("--enabled", action="store_true")
    p.add_argument("--disabled", action="store_true")

    # Set global flag
    p = subparsers.add_parser("set-global-flag")
    p.add_argument("feature")
    p.add_argument("--enabled", action="store_true")
    p.add_argument("--disabled", action="store_true")

    # List customers with feature
    p = subparsers.add_parser("list-customers")
    p.add_argument("feature")

    # List explicitly enabled customers
    p = subparsers.add_parser("list-customers-enabled")
    p.add_argument("feature")

    # List explicitly disabled customers
    p = subparsers.add_parser("list-customers-disabled")
    p.add_argument("feature")

    # List features for customer
    p = subparsers.add_parser("list-features")
    p.add_argument("customer_id", type=int)

    # List all features
    subparsers.add_parser("list-all-features")

    # Describe all features
    subparsers.add_parser("describe-all-features")

    # List all customers
    subparsers.add_parser("list-all-customers")

    args = parser.parse_args()
    store = SQLiteFeatureFlagStore(db_path=args.db_path)
    service = FeatureFlagService(store)

    if args.command == "add-feature":
        service.add_feature(args.name, default_enabled=args.default_enabled)
    elif args.command == "remove-feature":
        service.remove_feature(args.name)
    elif args.command == "rename-feature":
        service.rename_feature(args.old_name, args.new_name)
    elif args.command == "add-customer":
        service.add_customer(args.customer_id)
    elif args.command == "remove-customer":
        service.remove_customer(args.customer_id)
    elif args.command == "set-flag":
        if not (args.enabled ^ args.disabled):
            raise ValueError("Specify --enabled or --disabled, not both or neither")
        service.set_flag(args.feature, customer_id=args.customer_id, user_id=args.user_id, is_enabled=args.enabled)
    elif args.command == "set-global-flag":
        if not (args.enabled ^ args.disabled):
            raise ValueError("Specify --enabled or --disabled, not both or neither")
        service.set_global_flag(args.feature, is_enabled=args.enabled)
    elif args.command == "list-customers":
        print(service.list_customers_with_feature(args.feature))
    elif args.command == "list-customers-enabled":
        print(service.list_customers_with_feature_explicitly_enabled(args.feature))
    elif args.command == "list-customers-disabled":
        print(service.list_customers_with_feature_explicitly_disabled(args.feature))
    elif args.command == "list-features":
        print(service.list_features_for_customer(args.customer_id))
    elif args.command == "list-all-features":
        print(service.list_all_features())
    elif args.command == "describe-all-features":
        from pprint import pprint
        pprint(service.describe_all_features())
    elif args.command == "list-all-customers":
        print(service.list_all_customers())
    else:
        parser.print_help()

    service.close()

if __name__ == "__main__":
    main()