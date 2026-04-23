from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)

# Allow requests from frontend running on port 5500
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5500"}})

DB_NAME = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'merchant'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            merchant_id INTEGER NOT NULL,
            cardholder_name TEXT NOT NULL,
            masked_card TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            mode TEXT NOT NULL,
            reference TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            synced_at TEXT,
            FOREIGN KEY (merchant_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def log_action(action, details=""):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO audit_logs (action, details) VALUES (?, ?)",
        (action, details)
    )
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return "Flask backend is running"


@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not name or not email or not password:
            return jsonify({"message": "All fields are required"}), 400

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )
        conn.commit()
        conn.close()

        log_action("USER_REGISTERED", f"User registered: {email}")
        return jsonify({"message": "User registered successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"message": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"message": "Server error", "error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()
        conn.close()

        if not user:
            return jsonify({"message": "Invalid credentials"}), 401

        log_action("USER_LOGIN", f"User logged in: {email}")

        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        }), 200

    except Exception as e:
        return jsonify({"message": "Server error", "error": str(e)}), 500


@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    try:
        data = request.get_json()

        merchant_id = data.get("merchant_id")
        cardholder_name = data.get("cardholder_name", "").strip()
        masked_card = data.get("masked_card", "").strip()
        amount = data.get("amount")
        mode = data.get("mode", "").strip().lower()
        reference = data.get("reference", "").strip()

        if not merchant_id or not cardholder_name or not masked_card or not amount or not mode:
            return jsonify({"message": "Missing required fields"}), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"message": "Amount must be a valid number"}), 400

        if amount < 1 or amount > 50000:
            return jsonify({"message": "Amount must be between 1 and 50000"}), 400

        if mode not in ["online", "offline"]:
            return jsonify({"message": "Mode must be online or offline"}), 400

        conn = get_db_connection()

        # Check merchant exists
        merchant = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (merchant_id,)
        ).fetchone()

        if not merchant:
            conn.close()
            return jsonify({"message": "Merchant not found"}), 404

        # Prevent duplicate reference if provided
        if reference:
            existing = conn.execute(
                "SELECT * FROM transactions WHERE reference = ?",
                (reference,)
            ).fetchone()

            if existing:
                conn.close()
                return jsonify({"message": "Duplicate transaction reference detected"}), 409

        transaction_id = str(uuid.uuid4())[:8].upper()
        status = "authorized" if mode == "online" else "pending_sync"

        conn.execute("""
            INSERT INTO transactions
            (transaction_id, merchant_id, cardholder_name, masked_card, amount, status, mode, reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id,
            merchant_id,
            cardholder_name,
            masked_card,
            amount,
            status,
            mode,
            reference if reference else None
        ))

        conn.commit()
        conn.close()

        log_action(
            "TRANSACTION_CREATED",
            f"Transaction {transaction_id} created in {mode} mode with status {status}"
        )

        return jsonify({
            "message": "Transaction processed successfully",
            "transaction_id": transaction_id,
            "status": status
        }), 201

    except Exception as e:
        return jsonify({"message": "Server error", "error": str(e)}), 500


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    try:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT t.*, u.name AS merchant_name
            FROM transactions t
            JOIN users u ON t.merchant_id = u.id
            ORDER BY t.created_at DESC
        """).fetchall()
        conn.close()

        transactions = [dict(row) for row in rows]
        return jsonify(transactions), 200

    except Exception as e:
        return jsonify({"message": "Server error", "error": str(e)}), 500


@app.route("/api/sync", methods=["POST"])
def sync_transactions():
    try:
        conn = get_db_connection()

        pending = conn.execute("""
            SELECT * FROM transactions
            WHERE status = 'pending_sync'
        """).fetchall()

        synced_count = 0
        rejected_count = 0

        for txn in pending:
            # Simple prototype validation
            if txn["amount"] < 1 or txn["amount"] > 50000:
                conn.execute("""
                    UPDATE transactions
                    SET status = ?
                    WHERE id = ?
                """, ("rejected", txn["id"]))
                rejected_count += 1
            else:
                conn.execute("""
                    UPDATE transactions
                    SET status = ?, synced_at = ?
                    WHERE id = ?
                """, ("synced", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), txn["id"]))
                synced_count += 1

        conn.commit()
        conn.close()

        log_action(
            "SYNC_COMPLETED",
            f"Synced: {synced_count}, Rejected: {rejected_count}"
        )

        return jsonify({
            "message": f"Sync completed. Synced: {synced_count}, Rejected: {rejected_count}"
        }), 200

    except Exception as e:
        return jsonify({"message": "Server error", "error": str(e)}), 500


@app.route("/api/logs", methods=["GET"])
def get_logs():
    try:
        conn = get_db_connection()
        logs = conn.execute("""
            SELECT * FROM audit_logs
            ORDER BY created_at DESC
        """).fetchall()
        conn.close()

        return jsonify([dict(log) for log in logs]), 200

    except Exception as e:
        return jsonify({"message": "Server error", "error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True)