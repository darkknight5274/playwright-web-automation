from utils.logger import logger
import json
import os

def main():
    test_msg = "Validation test message"
    logger.info(test_msg, domain="test-domain")

    log_file = "logs/game_bot.log"
    if not os.path.exists(log_file):
        print(f"Error: {log_file} not found")
        return

    with open(log_file, "r") as f:
        lines = f.readlines()
        if not lines:
            print(f"Error: {log_file} is empty")
            return

        last_line = lines[-1].strip()
        try:
            log_entry = json.loads(last_line)
            if log_entry.get("event") == test_msg and log_entry.get("domain") == "test-domain":
                print("Validation successful: JSON log entry found in file with correct data.")
            else:
                print(f"Validation failed: Unexpected log entry {log_entry}")
        except json.JSONDecodeError:
            print(f"Validation failed: Could not decode JSON from {last_line}")

if __name__ == "__main__":
    main()
