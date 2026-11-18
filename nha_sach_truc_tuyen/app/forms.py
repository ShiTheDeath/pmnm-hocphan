from datetime import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from sqlalchemy import func
from wtforms import (
    IntegerField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    Email,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from . import db
from .models import Book, Category

MAX_COVER_BYTES = 2 * 1024 * 1024


class CheckoutForm(FlaskForm):
    full_name = StringField(
        "Họ tên", validators=[InputRequired("Vui lòng nhập họ tên."), Length(max=150)]
    )
    phone = StringField(
        "Số điện thoại",
        validators=[
            InputRequired("Vui lòng nhập số điện thoại."),
            Regexp(r"^0\d{9}$", message="Số điện thoại gồm 10 chữ số, bắt đầu bằng 0."),
        ],
    )
    email = StringField(
        "Email", validators=[Optional(), Email("Email không đúng định dạng."), Length(max=150)]
    )
    address = StringField(
        "Địa chỉ giao hàng",
        validators=[InputRequired("Vui lòng nhập địa chỉ giao hàng."), Length(max=300)],
    )
    note = TextAreaField("Ghi chú", validators=[Optional(), Length(max=500)])
    payment = RadioField(
        "Thanh toán",
        choices=[("cod", "Tiền mặt khi nhận hàng"), ("transfer", "Chuyển khoản")],
        default="cod",
        validators=[InputRequired("Vui lòng chọn hình thức thanh toán.")],
    )
    submit = SubmitField("Xác nhận đặt hàng")


class BookForm(FlaskForm):
    book_id = None  # gán id khi sửa để bỏ qua chính nó lúc kiểm tra trùng tên

    title = StringField(
        "Tên sách", validators=[InputRequired("Vui lòng nhập tên sách."), Length(max=200)]
    )
    author = StringField(
        "Tác giả", validators=[InputRequired("Vui lòng nhập tác giả."), Length(max=150)]
    )
    category_id = SelectField("Danh mục", coerce=int, validators=[InputRequired()])
    publisher = StringField("Nhà xuất bản", validators=[Optional(), Length(max=150)])
    year = IntegerField("Năm xuất bản", validators=[Optional()])
    price = IntegerField(
        "Giá (đồng)",
        validators=[
            InputRequired("Vui lòng nhập giá."),
            NumberRange(min=1000, message="Giá tối thiểu 1.000 đồng."),
        ],
    )
    stock = IntegerField(
        "Tồn kho",
        validators=[
            InputRequired("Vui lòng nhập tồn kho."),
            NumberRange(min=0, message="Tồn kho không âm."),
        ],
    )
    description = TextAreaField("Mô tả", validators=[Optional()])
    cover = FileField(
        "Ảnh bìa",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Chỉ nhận ảnh JPG, PNG hoặc WEBP."),
        ],
    )
    submit = SubmitField("Lưu")

    def validate_title(self, field):
        title = (field.data or "").strip()
        q = Book.query.filter(func.lower(Book.title) == title.lower())
        if self.book_id:
            q = q.filter(Book.id != self.book_id)
        if q.first():
            raise ValidationError("Tên sách đã tồn tại.")

    def validate_year(self, field):
        if field.data is not None and not (1900 <= field.data <= datetime.now().year):
            raise ValidationError(f"Năm xuất bản từ 1900 đến {datetime.now().year}.")

    def validate_category_id(self, field):
        if not db_category_exists(field.data):
            raise ValidationError("Danh mục không hợp lệ.")

    def validate_cover(self, field):
        f = field.data
        if f and getattr(f, "filename", ""):
            f.stream.seek(0, 2)
            size = f.stream.tell()
            f.stream.seek(0)
            if size > MAX_COVER_BYTES:
                raise ValidationError("Ảnh bìa tối đa 2 MB.")


def db_category_exists(cid):
    return db.session.get(Category, cid) is not None


class CategoryForm(FlaskForm):
    category_id = None  # gán id khi sửa

    name = StringField(
        "Tên", validators=[InputRequired("Vui lòng nhập tên danh mục."), Length(max=100)]
    )
    description = TextAreaField("Mô tả", validators=[Optional()])
    submit = SubmitField("Thêm")

    def validate_name(self, field):
        name = (field.data or "").strip()
        q = Category.query.filter(func.lower(Category.name) == name.lower())
        if self.category_id:
            q = q.filter(Category.id != self.category_id)
        if q.first():
            raise ValidationError("Danh mục đã tồn tại.")