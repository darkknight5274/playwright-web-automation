from activities.registry import ActivityRegistry
from utils.logger import logger
import json
import os

def main():
    # 1. Validate Registry
    paths = ActivityRegistry.get_all_paths()
    print(f"Registered paths: {paths}")

    home_activity = ActivityRegistry.get_activity("/home")
    if home_activity and home_activity.path == "/home":
        print("Registry validation successful: HomeActivity found.")
    else:
        print("Registry validation failed.")

    # 2. Validate Logger
    test_msg = "Final validation message"
    logger.info(test_msg, domain="test-domain")

    log_file = "logs/game_bot.log"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            last_line = f.readlines()[-1].strip()
            log_entry = json.loads(last_line)
            if log_entry.get("event") == test_msg:
                print("Logger validation successful: JSON entry found.")
            else:
                print("Logger validation failed.")

if __name__ == "__main__":
    main()
