import os
import uuid
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import func, or_

from . import db
from .forms import BookForm, CategoryForm
from .models import STATUS_LABELS, Book, Category, Order

bp = Blueprint("admin", __name__)


# Dashboard
@bp.route("/")
def dashboard():
    low = current_app.config["LOW_STOCK"]
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stats = {
        "books": db.session.query(func.count(Book.id)).scalar(),
        "pending": db.session.query(func.count(Order.id)).filter(Order.status == "pending").scalar(),
        "revenue": db.session.query(func.coalesce(func.sum(Order.total), 0))
        .filter(Order.status == "completed", Order.created_at >= month_start)
        .scalar(),
        "low": db.session.query(func.count(Book.id)).filter(Book.stock <= low).scalar(),
    }
    latest = Order.query.order_by(Order.created_at.desc(), Order.id.desc()).limit(5).all()
    low_books = Book.query.filter(Book.stock <= low).order_by(Book.stock, Book.title).all()

    # Doanh thu 7 ngày gần nhất (đơn Hoàn tất)
    today = now.date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    rows = (
        db.session.query(func.date(Order.created_at), func.sum(Order.total))
        .filter(Order.status == "completed", Order.created_at >= datetime.combine(days[0], datetime.min.time()))
        .group_by(func.date(Order.created_at))
        .all()
    )
    by_day = {str(d): int(s) for d, s in rows}
    chart = [{"label": d.strftime("%d/%m"), "value": by_day.get(d.isoformat(), 0)} for d in days]
    top = max((c["value"] for c in chart), default=0) or 1
    for c in chart:
        c["pct"] = max(round(c["value"] * 100 / top), 3 if c["value"] else 1)

    return render_template(
        "admin/dashboard.html", stats=stats, latest=latest, low_books=low_books,
        chart=chart, low=low, month=now.month,
    )


# Quản lý sách 
@bp.route("/books")
def books():
    low = current_app.config["LOW_STOCK"]
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", type=int)
    stock = request.args.get("stock", "")
    page = request.args.get("page", 1, type=int)

    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Book.title.ilike(like), Book.author.ilike(like)))
    if cat:
        query = query.filter(Book.category_id == cat)
    if stock == "in":
        query = query.filter(Book.stock > 0)
    elif stock == "low":
        query = query.filter(Book.stock <= low)
    elif stock == "out":
        query = query.filter(Book.stock == 0)

    pagination = query.order_by(Book.created_at.desc(), Book.id.desc()).paginate(
        page=page, per_page=5, error_out=False
    )
    return render_template(
        "admin/books.html", pagination=pagination, categories=Category.query.order_by(Category.name).all(),
        q=q, cat=cat, stock=stock, low=low,
    )


def _save_cover(form, book):
    """Lưu ảnh mới với tên ngẫu nhiên, xoá ảnh cũ. Không chọn ảnh thì giữ ảnh cũ."""
    f = form.cover.data
    if f and getattr(f, "filename", ""):
        ext = f.filename.rsplit(".", 1)[-1].lower()
        name = f"{uuid.uuid4().hex}.{ext}"
        f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
        book.delete_cover_file()
        book.cover = name


def _fill_book(form, book):
    book.title = form.title.data.strip()
    book.author = form.author.data.strip()
    book.category_id = form.category_id.data
    book.publisher = (form.publisher.data or "").strip() or None
    book.year = form.year.data
    book.price = form.price.data
    book.stock = form.stock.data
    book.description = (form.description.data or "").strip() or None
    _save_cover(form, book)


def _book_form(book=None):
    form = BookForm(obj=book)
    form.book_id = book.id if book else None
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name)]
    return form


@bp.route("/books/new", methods=["GET", "POST"])
def book_new():
    form = _book_form()
    if not form.category_id.choices:
        flash("Hãy tạo ít nhất một danh mục trước khi thêm sách.", "warning")
        return redirect(url_for("admin.categories"))
    if form.validate_on_submit():
        book = Book()
        _fill_book(form, book)
        db.session.add(book)
        db.session.commit()
        flash(f"Đã thêm sách “{book.title}”.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", form=form, book=None)


@bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def book_edit(book_id):
    book = db.get_or_404(Book, book_id)
    form = _book_form(book)
    if form.validate_on_submit():
        _fill_book(form, book)
        db.session.commit()
        flash(f"Đã cập nhật sách “{book.title}”.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", form=form, book=book)


@bp.post("/books/<int:book_id>/delete")
def book_delete(book_id):
    book = db.get_or_404(Book, book_id)
    if book.has_orders:
        flash(f"Không thể xoá “{book.title}”: sách đã có trong đơn hàng.", "danger")
        return redirect(request.referrer or url_for("admin.books"))
    book.delete_cover_file()
    title = book.title
    db.session.delete(book)
    db.session.commit()
    flash(f"Đã xoá sách “{title}”.", "success")
    return redirect(url_for("admin.books"))


# Danh mục sách 
def _category_rows():
    return (
        db.session.query(Category, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
        .all()
    )


@bp.route("/categories", methods=["GET", "POST"])
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        db.session.add(
            Category(name=form.name.data.strip(), description=(form.description.data or "").strip() or None)
        )
        db.session.commit()
        flash("Đã thêm danh mục.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/categories.html", rows=_category_rows(), form=form, editing=None)


@bp.route("/categories/<int:cat_id>/edit", methods=["GET", "POST"])
def category_edit(cat_id):
    cat = db.get_or_404(Category, cat_id)
    form = CategoryForm(obj=cat)
    form.category_id = cat.id
    form.submit.label.text = "Lưu"
    if form.validate_on_submit():
        cat.name = form.name.data.strip()
        cat.description = (form.description.data or "").strip() or None
        db.session.commit()
        flash("Đã cập nhật danh mục.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/categories.html", rows=_category_rows(), form=form, editing=cat)


@bp.post("/categories/<int:cat_id>/delete")
def category_delete(cat_id):
    cat = db.get_or_404(Category, cat_id)
    n = db.session.query(func.count(Book.id)).filter(Book.category_id == cat.id).scalar()
    if n:
        flash(f"Không thể xoá “{cat.name}”: còn {n} sách.", "danger")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash(f"Đã xoá danh mục “{cat.name}”.", "success")
    return redirect(url_for("admin.categories"))


# Danh sách đơn hàng 
@bp.route("/orders")
def orders():
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    conds = []
    if status in STATUS_LABELS:
        conds.append(Order.status == status)
    else:
        status = ""
    if q:
        like = f"%{q}%"
        terms = [Order.customer_name.ilike(like), Order.phone.ilike(like)]
        digits = q.lstrip("#")
        if digits.isdigit():
            terms.append(Order.id == int(digits))
        conds.append(or_(*terms))

    counts = dict(db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all())
    counts_all = sum(counts.values())

    pagination = (
        Order.query.filter(*conds)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    n_orders, sum_total = db.session.query(
        func.count(Order.id), func.coalesce(func.sum(Order.total), 0)
    ).filter(*conds).one()

    return render_template(
        "admin/orders.html", pagination=pagination, status=status, q=q, counts=counts,
        counts_all=counts_all, n_orders=n_orders, sum_total=sum_total,
    )


# Chi tiết đơn hàng 
@bp.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template("admin/order_detail.html", order=order)


def _change_status(order, new_status):
    if new_status not in order.allowed_next:
        flash(
            f"Không thể chuyển từ “{order.status_label}” sang “{STATUS_LABELS.get(new_status, new_status)}”.",
            "danger",
        )
        return False
    if new_status == "cancelled":
        for item in order.items:  # huỷ đơn: hoàn lại tồn kho
            item.book.stock += item.quantity
    order.status = new_status
    order.add_history(new_status)
    db.session.commit()
    flash(f"Đã chuyển đơn #{order.id} sang “{order.status_label}”.", "success")
    return True


@bp.post("/orders/<int:order_id>/status")
def order_status(order_id):
    order = db.get_or_404(Order, order_id)
    _change_status(order, request.form.get("status", ""))
    return redirect(url_for("admin.order_detail", order_id=order.id))


@bp.post("/orders/<int:order_id>/cancel")
def order_cancel(order_id):
    order = db.get_or_404(Order, order_id)
    _change_status(order, "cancelled")
    return redirect(url_for("admin.order_detail", order_id=order.id))