import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "books.db")

app = Flask(__name__)
app.secret_key = "dev-secret-key"

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS books (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    author      TEXT NOT NULL,
    price       REAL NOT NULL DEFAULT 0 CHECK (price >= 0),
    quantity    INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    year        INTEGER,
    category_id INTEGER NOT NULL,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_books_category ON books(category_id);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(seed=True):
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    if seed and db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        cats = [("Công nghệ thông tin", "Lập trình, CSDL, mạng"),
                ("Văn học", "Tiểu thuyết, truyện ngắn, thơ"),
                ("Kinh tế", "Quản trị, tài chính, marketing"),
                ("Khoa học", "Toán, lý, hóa, sinh")]
        db.executemany("INSERT INTO categories(name, description) VALUES (?, ?)", cats)
        books = [
            ("Lập trình Python cơ bản", "Nguyễn Văn A", 120000, 25, 2022, 1),
            ("Cơ sở dữ liệu SQL Server", "Trần Thị B", 150000, 10, 2021, 1),
            ("Phát triển web với Flask", "Lê Văn C", 135000, 8, 2023, 1),
            ("Dế Mèn phiêu lưu ký", "Tô Hoài", 55000, 40, 2019, 2),
            ("Truyện Kiều", "Nguyễn Du", 70000, 15, 2018, 2),
            ("Quản trị học", "Phạm Thị D", 98000, 12, 2020, 3),
            ("Marketing căn bản", "Hoàng Văn E", 105000, 0, 2021, 3),
            ("Vật lý đại cương", "Đỗ Văn F", 88000, 5, 2017, 4),
        ]
        db.executemany(
            "INSERT INTO books(title, author, price, quantity, year, category_id) "
            "VALUES (?, ?, ?, ?, ?, ?)", books)
    db.commit()
    db.close()


@app.template_filter("vnd")
def vnd(value):
    return f"{int(value or 0):,}".replace(",", ".") + " ₫"


# ---------------------------------------------------------------- Dashboard
@app.route("/")
def dashboard():
    db = get_db()
    totals = db.execute(
        "SELECT (SELECT COUNT(*) FROM categories) AS n_cat, "
        "COUNT(*) AS n_book, COALESCE(SUM(quantity),0) AS n_qty, "
        "COALESCE(SUM(price*quantity),0) AS stock_value FROM books").fetchone()
    per_cat = db.execute(
        "SELECT c.id, c.name, COUNT(b.id) AS n_book, "
        "COALESCE(SUM(b.quantity),0) AS n_qty, "
        "COALESCE(SUM(b.price*b.quantity),0) AS value "
        "FROM categories c LEFT JOIN books b ON b.category_id = c.id "
        "GROUP BY c.id ORDER BY n_book DESC, c.name").fetchall()
    low_stock = db.execute(
        "SELECT b.*, c.name AS cat_name FROM books b JOIN categories c "
        "ON c.id = b.category_id WHERE b.quantity <= 5 ORDER BY b.quantity, b.title"
    ).fetchall()
    latest = db.execute(
        "SELECT b.*, c.name AS cat_name FROM books b JOIN categories c "
        "ON c.id = b.category_id ORDER BY b.id DESC LIMIT 5").fetchall()
    max_book = max([r["n_book"] for r in per_cat] + [1])
    return render_template("dashboard.html", totals=totals, per_cat=per_cat,
                           low_stock=low_stock, latest=latest, max_book=max_book)


# ------------------------------------------------------------ Categories CRUD
@app.route("/categories")
def categories():
    q = request.args.get("q", "").strip()
    rows = get_db().execute(
        "SELECT c.*, COUNT(b.id) AS n_book FROM categories c "
        "LEFT JOIN books b ON b.category_id = c.id "
        "WHERE c.name LIKE ? GROUP BY c.id ORDER BY c.name", (f"%{q}%",)).fetchall()
    return render_template("categories.html", rows=rows, q=q)


@app.route("/categories/new", methods=["GET", "POST"])
def category_new():
    return _category_form(None)


@app.route("/categories/<int:cid>/edit", methods=["GET", "POST"])
def category_edit(cid):
    row = get_db().execute("SELECT * FROM categories WHERE id=?", (cid,)).fetchone()
    if row is None:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("categories"))
    return _category_form(row)


def _category_form(row):
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "").strip()
        if not name:
            flash("Tên danh mục không được để trống.", "error")
            return render_template("category_form.html", row=request.form, editing=row is not None)
        db = get_db()
        try:
            if row is None:
                db.execute("INSERT INTO categories(name, description) VALUES (?, ?)", (name, desc))
                flash("Đã thêm danh mục.", "ok")
            else:
                db.execute("UPDATE categories SET name=?, description=? WHERE id=?",
                           (name, desc, row["id"]))
                flash("Đã cập nhật danh mục.", "ok")
            db.commit()
            return redirect(url_for("categories"))
        except sqlite3.IntegrityError:
            flash("Tên danh mục đã tồn tại.", "error")
            return render_template("category_form.html", row=request.form, editing=row is not None)
    return render_template("category_form.html", row=row or {}, editing=row is not None)


@app.route("/categories/<int:cid>/delete", methods=["POST"])
def category_delete(cid):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id=?", (cid,))  # sách bị xóa theo (CASCADE)
    db.commit()
    flash("Đã xóa danh mục và các sách thuộc danh mục.", "ok")
    return redirect(url_for("categories"))


# ------------------------------------------------------------------ Books CRUD
@app.route("/books")
def books():
    db = get_db()
    cat_id = request.args.get("category_id", type=int)
    q = request.args.get("q", "").strip()
    sql = ("SELECT b.*, c.name AS cat_name FROM books b JOIN categories c "
           "ON c.id = b.category_id WHERE (b.title LIKE ? OR b.author LIKE ?)")
    params = [f"%{q}%", f"%{q}%"]
    if cat_id:
        sql += " AND b.category_id = ?"
        params.append(cat_id)
    sql += " ORDER BY c.name, b.title"
    rows = db.execute(sql, params).fetchall()
    cats = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    current = next((c for c in cats if c["id"] == cat_id), None)
    return render_template("books.html", rows=rows, cats=cats, cat_id=cat_id,
                           current=current, q=q)


@app.route("/books/new", methods=["GET", "POST"])
def book_new():
    return _book_form(None)


@app.route("/books/<int:bid>/edit", methods=["GET", "POST"])
def book_edit(bid):
    row = get_db().execute("SELECT * FROM books WHERE id=?", (bid,)).fetchone()
    if row is None:
        flash("Không tìm thấy sách.", "error")
        return redirect(url_for("books"))
    return _book_form(row)


def _book_form(row):
    db = get_db()
    cats = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    if not cats:
        flash("Hãy tạo danh mục trước khi thêm sách.", "error")
        return redirect(url_for("category_new"))
    if request.method == "POST":
        f = request.form
        title, author = f.get("title", "").strip(), f.get("author", "").strip()
        try:
            price = float(f.get("price") or 0)
            qty = int(f.get("quantity") or 0)
            year = int(f["year"]) if f.get("year") else None
            cat_id = int(f.get("category_id"))
        except (ValueError, TypeError):
            flash("Giá, số lượng, năm, danh mục phải là số hợp lệ.", "error")
            return render_template("book_form.html", row=f, cats=cats, editing=row is not None)
        if not title or not author or price < 0 or qty < 0:
            flash("Vui lòng nhập tên sách, tác giả; giá và số lượng không âm.", "error")
            return render_template("book_form.html", row=f, cats=cats, editing=row is not None)
        if row is None:
            db.execute("INSERT INTO books(title, author, price, quantity, year, category_id) "
                       "VALUES (?,?,?,?,?,?)", (title, author, price, qty, year, cat_id))
            flash("Đã thêm sách.", "ok")
        else:
            db.execute("UPDATE books SET title=?, author=?, price=?, quantity=?, year=?, "
                       "category_id=? WHERE id=?", (title, author, price, qty, year, cat_id, row["id"]))
            flash("Đã cập nhật sách.", "ok")
        db.commit()
        return redirect(url_for("books", category_id=cat_id))
    default = row or {"category_id": request.args.get("category_id", type=int)}
    return render_template("book_form.html", row=default, cats=cats, editing=row is not None)


@app.route("/books/<int:bid>/delete", methods=["POST"])
def book_delete(bid):
    db = get_db()
    row = db.execute("SELECT category_id FROM books WHERE id=?", (bid,)).fetchone()
    db.execute("DELETE FROM books WHERE id=?", (bid,))
    db.commit()
    flash("Đã xóa sách.", "ok")
    return redirect(url_for("books", category_id=row["category_id"] if row else None))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)