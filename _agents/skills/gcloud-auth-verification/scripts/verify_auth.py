import json
import subprocess
import sys

def get_gcloud_accounts():
    try:
        # Run gcloud auth list in JSON format
        result = subprocess.run(
            ["gcloud", "auth", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8"
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(json.dumps({"error": f"Failed to retrieve gcloud accounts: {e}"}))
        sys.exit(1)

def main():
    accounts = get_gcloud_accounts()
    active_account = None
    other_accounts = []

    for entry in accounts:
        account = entry.get("account")
        status = entry.get("status", "")
        if status == "ACTIVE":
            active_account = account
        else:
            other_accounts.append(account)

    output = {
        "active_account": active_account,
        "other_accounts": other_accounts
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
