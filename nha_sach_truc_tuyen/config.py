import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dangquangpmnm")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "book_manager.db")
    )
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # chặn request quá lớn; ảnh bìa tối đa 2 MB kiểm tra riêng

    SHIPPING_FEE = 20000
    FREE_SHIP_FROM = 200000
    LOW_STOCK = 5