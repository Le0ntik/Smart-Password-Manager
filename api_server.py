from flask import Flask, request, jsonify, render_template
from vault.vault import Vault
from vault.entry import Entry
from crypto.crypto_engine import CryptoEngine
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

MASTER_KEY_PATH = os.getenv("MASTER_KEY_PATH", "data/master.key")
VAULT_PATH = os.getenv("VAULT_PATH", "data/vault.enc")

# Загружаем ключ шифрования
with open(MASTER_KEY_PATH, "rb") as f:
    key = f.read()


# Создаём объект шифрования
crypto = CryptoEngine(key)


# Создаём хранилище
vault = Vault(crypto, filename=VAULT_PATH)
vault.load()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/entries", methods=["GET"])
def get_entries():
    return jsonify([entry.__dict__ for entry in vault.entries])


@app.route("/add", methods=["POST"])
def add_entry():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Нет данных в запросе"}), 400

    title = data.get("title", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    note = data.get("note", "").strip()

    if not title or not username or not password:
        return jsonify({
            "error": "Поля title, username и password обязательны"
        }), 400

    entry = Entry(
        title=title,
        username=username,
        password=password,
        note=note
    )

    vault.add_entry(entry)
    vault.save()

    return jsonify({
        "status": "ok",
        "entry": entry.__dict__
    }), 201


@app.route("/delete/<int:index>", methods=["DELETE"])
def delete_entry(index):
    if index < 0 or index >= len(vault.entries):
        return jsonify({"error": "Запись не найдена"}), 404

    deleted_entry = vault.entries.pop(index)
    vault.save()

    return jsonify({
        "status": "deleted",
        "entry": deleted_entry.__dict__
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)