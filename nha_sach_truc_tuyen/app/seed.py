import sqlite3
from datetime import datetime, timedelta

import click
from sqlalchemy import func

from . import db
from .models import Book, Category, Order, OrderItem

# Dữ liệu từ app2.py ở bài kiểm tra tuần trước (book_manager)
CATEGORIES = [
    ("Công nghệ thông tin", "Lập trình, CSDL, mạng"),
    ("Văn học", "Tiểu thuyết, truyện ngắn, thơ"),
    ("Kinh tế", "Quản trị, tài chính, marketing"),
    ("Khoa học", "Toán, lý, hóa, sinh"),
]

BOOKS = [
    ("Lập trình Python cơ bản", "Nguyễn Văn A", 120000, 25, 2022, "Công nghệ thông tin"),
    ("Cơ sở dữ liệu SQL Server", "Trần Thị B", 150000, 10, 2021, "Công nghệ thông tin"),
    ("Phát triển web với Flask", "Lê Văn C", 135000, 8, 2023, "Công nghệ thông tin"),
    ("Dế Mèn phiêu lưu ký", "Tô Hoài", 55000, 40, 2019, "Văn học"),
    ("Truyện Kiều", "Nguyễn Du", 70000, 15, 2018, "Văn học"),
    ("Quản trị học", "Phạm Thị D", 98000, 12, 2020, "Kinh tế"),
    ("Marketing căn bản", "Hoàng Văn E", 105000, 0, 2021, "Kinh tế"),
    ("Vật lý đại cương", "Đỗ Văn F", 88000, 5, 2017, "Khoa học"),
]

DEMO_ORDERS = [
    ("Nguyễn Văn An", "0912345678", "12 Lê Lợi, phường Thuận Hoá, Huế", "pending", 0,
     [("Lập trình Python cơ bản", 2), ("Phát triển web với Flask", 1)]),
    ("Hoàng Thu Hà", "0987654321", "5 Hùng Vương, Huế", "pending", 1,
     [("Truyện Kiều", 1), ("Dế Mèn phiêu lưu ký", 2)]),
    ("Trần Thị Bình", "0905111222", "20 Trần Phú, Huế", "shipping", 2,
     [("Quản trị học", 1), ("Vật lý đại cương", 1)]),
    ("Lê Hoàng Cường", "0933444555", "8 Nguyễn Huệ, Huế", "completed", 3,
     [("Cơ sở dữ liệu SQL Server", 1)]),
    ("Phạm Minh Dũng", "0977888999", "30 Điện Biên Phủ, Huế", "cancelled", 4,
     [("Truyện Kiều", 1)]),
]


def _category_by_name(name):
    return Category.query.filter(func.lower(Category.name) == name.lower()).first()


def seed_basic():
    for name, desc in CATEGORIES:
        if not _category_by_name(name):
            db.session.add(Category(name=name, description=desc))
    db.session.flush()
    for title, author, price, stock, year, cat in BOOKS:
        if not Book.query.filter(func.lower(Book.title) == title.lower()).first():
            db.session.add(Book(title=title, author=author, price=price, stock=stock,
                                year=year, category=_category_by_name(cat)))
    db.session.commit()


def seed_demo_orders():
    """Đơn mẫu để xem trang quản trị; không trừ tồn kho."""
    if Order.query.count():
        return
    now = datetime.now()
    for name, phone, addr, status, days, lines in DEMO_ORDERS:
        order = Order(customer_name=name, phone=phone, address=addr, payment="cod",
                      status=status, created_at=now - timedelta(days=days), subtotal=0,
                      shipping_fee=0, total=0)
        subtotal = 0
        for title, qty in lines:
            book = Book.query.filter_by(title=title).one()
            order.items.append(OrderItem(book=book, unit_price=book.price, quantity=qty))
            subtotal += book.price * qty
        order.subtotal = subtotal
        order.shipping_fee = 0 if subtotal >= 200000 else 20000
        order.total = subtotal + order.shipping_fee
        order.add_history("pending", "Đặt hàng")
        if status != "pending":
            order.add_history(status)
        db.session.add(order)
    db.session.commit()


def import_old(path):
    """Nhập danh mục và sách từ books.db cũ (sqlite3). Bỏ qua mục đã có.
    Đổi tên cột: quantity -> stock, price REAL -> số nguyên đồng."""
    src = sqlite3.connect(path)
    src.row_factory = sqlite3.Row
    added_c = added_b = skipped = 0
    id_map = {}
    for row in src.execute("SELECT * FROM categories ORDER BY id"):
        cat = _category_by_name(row["name"])
        if cat is None:
            cat = Category(name=row["name"], description=row["description"] or None)
            db.session.add(cat)
            added_c += 1
        id_map[row["id"]] = cat
    db.session.flush()
    for row in src.execute("SELECT * FROM books ORDER BY id"):
        if Book.query.filter(func.lower(Book.title) == row["title"].lower()).first():
            skipped += 1
            continue
        db.session.add(Book(
            title=row["title"], author=row["author"], price=int(round(row["price"])),
            stock=row["quantity"], year=row["year"], category=id_map[row["category_id"]],
        ))
        added_b += 1
    db.session.commit()
    src.close()
    return added_c, added_b, skipped


def register_cli(app):
    @app.cli.command("seed")
    @click.option("--demo", is_flag=True, help="Thêm cả đơn hàng mẫu")
    def seed(demo):
        seed_basic()
        if demo:
            seed_demo_orders()
        click.echo("Đã thêm dữ liệu mẫu.")

    @app.cli.command("import-old")
    @click.argument("path", type=click.Path(exists=True, dir_okay=False))
    def import_old_cmd(path):
        c, b, s = import_old(path)
        click.echo(f"Đã nhập {c} danh mục, {b} sách (bỏ qua {s} sách đã có).")