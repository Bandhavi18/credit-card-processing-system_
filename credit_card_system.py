import time
import random




offline_storage = []
processed_transactions = set()
logs = []

network_available = True   # Change this to simulate network



def generate_transaction_id():
    return "TXN" + str(int(time.time() * 1000)) + str(random.randint(100, 999))


def log_event(message):
    logs.append(message)
    print("[LOG]:", message)


def is_network_available():
    return network_available



def validate_card(card_number):
    return len(card_number) == 16 and card_number.isdigit()


def validate_amount(amount):
    return 0 < amount <= 50000


def is_duplicate(txn_id):
    return txn_id in processed_transactions



def store_offline(transaction):
    offline_storage.append(transaction)
    log_event(f"Stored OFFLINE: {transaction['id']}")



def send_to_bank(transaction):
    print(f"Processing with bank: {transaction['id']}")
    time.sleep(1)
    return True  # always success for demo



def process_transaction():
    global network_available

    card = input("Enter Card Number (16 digits): ")
    amount = float(input("Enter Amount: "))

    if not validate_card(card):
        print("Invalid Card!")
        return

    if not validate_amount(amount):
        print("Invalid Amount!")
        return

    txn_id = generate_transaction_id()

    if is_duplicate(txn_id):
        print("Duplicate Transaction!")
        return

    transaction = {
        "id": txn_id,
        "card": card[-4:],  # mask card
        "amount": amount,
        "status": "PENDING"
    }

    if is_network_available():
        print("ONLINE MODE")
        success = send_to_bank(transaction)
        if success:
            transaction["status"] = "SUCCESS"
            processed_transactions.add(txn_id)
            log_event(f"Processed ONLINE: {txn_id}")
    else:
        print("OFFLINE MODE")
        transaction["status"] = "STORED"
        store_offline(transaction)



def sync_transactions():
    global offline_storage

    if not is_network_available():
        print("Network still offline. Cannot sync.")
        return

    print("\n--- Synchronizing Transactions ---")

    remaining = []

    for txn in offline_storage:
        if txn["id"] in processed_transactions:
            log_event(f"Duplicate skipped: {txn['id']}")
            continue

        success = send_to_bank(txn)

        if success:
            txn["status"] = "SUCCESS"
            processed_transactions.add(txn["id"])
            log_event(f"Synchronized: {txn['id']}")
        else:
            remaining.append(txn)

    offline_storage = remaining



def view_offline_transactions():
    print("\n--- Offline Transactions ---")
    for txn in offline_storage:
        print(txn)


def view_logs():
    print("\n--- Logs ---")
    for log in logs:
        print(log)



def main():
    global network_available

    while True:
        print("\n====== CREDIT CARD SYSTEM ======")
        print("1. Make Transaction")
        print("2. Toggle Network")
        print("3. Sync Transactions")
        print("4. View Offline Transactions")
        print("5. View Logs")
        print("6. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            process_transaction()

        elif choice == "2":
            network_available = not network_available
            print("Network is now", "ONLINE" if network_available else "OFFLINE")

        elif choice == "3":
            sync_transactions()

        elif choice == "4":
            view_offline_transactions()

        elif choice == "5":
            view_logs()

        elif choice == "6":
            print("Exiting...")
            break

        else:
            print("Invalid choice!")



if __name__ == "__main__":
    main()