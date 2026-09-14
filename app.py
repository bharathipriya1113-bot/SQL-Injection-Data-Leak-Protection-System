from flask import Flask, request
import sqlite3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

app = Flask(__name__)

AES_KEY = b"0123456789abcdef0123456789abcdef"
CAPABILITY_CODE = "SECURE2026"
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_data(data):
    nonce = os.urandom(12)

    aes = AESGCM(AES_KEY)

    encrypted_data = aes.encrypt(
        nonce,
        data.encode(),
        None
    )

    return nonce, encrypted_data


def decrypt_data(nonce, encrypted_data):
    aes = AESGCM(AES_KEY)

    decrypted_data = aes.decrypt(
        nonce,
        encrypted_data,
        None
    )

    return decrypted_data.decode()


def get_database():
    connection = sqlite3.connect("users.db")
    connection.row_factory = sqlite3.Row
    return connection


# Create database and table
connection = get_database()

connection.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    encrypted_password BLOB NOT NULL,
    nonce BLOB NOT NULL
)
""")

connection.commit()
connection.close()


@app.route("/")
def home():
    return """
    <h1>SQL Injection Data Leak Protection System</h1>

    <form action="/login" method="POST">
        <input type="text" name="username" placeholder="Username">
        <input type="password" name="password" placeholder="Password">
        <input type="text" name="capability_code" placeholder="Capability Code">
        <button type="submit">Login</button>
    </form>
    """

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]
    capability_code = request.form["capability_code"]

    if capability_code != CAPABILITY_CODE:
      return "<h2>Access Denied ❌ - Invalid Capability Code</h2>"
    connection = get_database()

    # Parameterized query prevents SQL Injection
    query = "SELECT * FROM users WHERE username = ?"

    result = connection.execute(
        query,
        (username,)
    ).fetchone()

    if result:
        try:
            decrypted_password = decrypt_data(
                result["nonce"],
                result["encrypted_password"]
            )

            if decrypted_password == password:
                connection.close()
                return "<h2>Login Successful ✅</h2>"

        except Exception:
            pass

    connection.close()
    return "<h2>Invalid username or password ❌</h2>"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)