from flask import Blueprint, jsonify, render_template, request
import mysql.connector
from config import DB_CONFIG

api_bp = Blueprint("api", __name__)


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def barang_json(row):
    data = dict(row)
    data["harga"] = float(data["harga"])
    return data


def validasi_barang(data):
    """Mengembalikan (nama, harga, stok, error). Jika valid, error = None."""
    if not isinstance(data, dict):
        return None, None, None, "Body harus berupa JSON"

    nama = data.get("nama")
    if not isinstance(nama, str) or not nama.strip():
        return None, None, None, "Nama barang wajib diisi"

    try:
        harga = float(data.get("harga"))
        stok = int(data.get("stok"))
        if not 0 <= harga < float("inf") or stok < 0:
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        return None, None, None, "Harga dan stok tidak valid"

    return nama.strip(), harga, stok, None


@api_bp.route("/")
def index():
    return render_template("index.html")


# Mengambil semua barang yang ada di database
@api_bp.route("/api/barang", methods=["GET"])
def get_barang():
    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM barang ORDER BY id")
        rows = cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()

    return jsonify([barang_json(row) for row in rows])


# Menambahkan barang
@api_bp.route("/api/barang", methods=["POST"])
def create_barang():
    data = request.get_json(silent=True)
    nama, harga, stok, error = validasi_barang(data)
    if error:
        return jsonify({"error": error}), 400

    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO barang (nama, harga, stok) VALUES (%s, %s, %s)",
            (nama, harga, stok),
        )
        barang_id = cursor.lastrowid
        cursor.execute("SELECT * FROM barang WHERE id = %s", (barang_id,))
        row = cursor.fetchone()
        conn.commit()
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()

    return jsonify(barang_json(row)), 201


# Memperbarui barang berdasarkan ID
@api_bp.route("/api/barang/<int:id>", methods=["PUT"])
def update_barang(id):
    data = request.get_json(silent=True)
    nama, harga, stok, error = validasi_barang(data)
    if error:
        return jsonify({"error": error}), 400

    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "UPDATE barang SET nama = %s, harga = %s, stok = %s WHERE id = %s",
            (nama, harga, stok, id),
        )
        cursor.execute("SELECT * FROM barang WHERE id = %s", (id,))
        row = cursor.fetchone()
        if row is not None:
            conn.commit()
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()

    if row is None:
        return jsonify({"error": "Barang tidak ditemukan"}), 404

    return jsonify(barang_json(row))


# Menghapus barang berdasarkan ID
@api_bp.route("/api/barang/<int:id>", methods=["DELETE"])
def delete_barang(id):
    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM barang WHERE id = %s", (id,))
        deleted = cursor.rowcount > 0
        if deleted:
            conn.commit()
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()

    if not deleted:
        return jsonify({"error": "Barang tidak ditemukan"}), 404

    return jsonify({"message": "Barang berhasil dihapus"})