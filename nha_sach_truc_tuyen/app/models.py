import os
from datetime import datetime

from flask import current_app, url_for

from . import db

# Trạng thái đơn hàng: khoá lưu trong CSDL 
STATUS_LABELS = {
    "pending": "Chờ xác nhận",
    "shipping": "Đang giao",
    "completed": "Hoàn tất",
    "cancelled": "Đã huỷ",
}

# Chuyển trạng thái hợp lệ
STATUS_FLOW = {
    "pending": ["shipping", "cancelled"],
    "shipping": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}

PAYMENT_LABELS = {
    "cod": "Tiền mặt khi nhận hàng",
    "transfer": "Chuyển khoản",
}


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)

    books = db.relationship("Book", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(150))
    year = db.Column(db.Integer)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text)
    cover = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    category = db.relationship("Category", back_populates="books")

    @property
    def cover_url(self):
        if self.cover:
            return url_for("static", filename="uploads/" + self.cover)
        return None

    @property
    def has_orders(self):
        return db.session.query(OrderItem.id).filter_by(book_id=self.id).first() is not None

    def delete_cover_file(self):
        if self.cover:
            path = os.path.join(current_app.config["UPLOAD_FOLDER"], self.cover)
            if os.path.exists(path):
                os.remove(path)

    def __repr__(self):
        return f"<Book {self.title}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150))
    address = db.Column(db.String(300), nullable=False)
    note = db.Column(db.Text)
    payment = db.Column(db.String(20), nullable=False, default="cod")
    subtotal = db.Column(db.Integer, nullable=False)
    shipping_fee = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)

    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    history = db.relationship(
        "OrderHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderHistory.changed_at, OrderHistory.id",
    )

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def payment_label(self):
        return PAYMENT_LABELS.get(self.payment, self.payment)

    @property
    def allowed_next(self):
        return STATUS_FLOW.get(self.status, [])

    def add_history(self, status, note=None):
        self.history.append(OrderHistory(status=status, note=note, changed_at=datetime.now()))


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)  # giá tại thời điểm đặt
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", back_populates="items")
    book = db.relationship("Book")

    @property
    def amount(self):
        return self.unit_price * self.quantity


class OrderHistory(db.Model):
    __tablename__ = "order_history"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(200))
    changed_at = db.Column(db.DateTime, default=datetime.now)

    order = db.relationship("Order", back_populates="history")

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)