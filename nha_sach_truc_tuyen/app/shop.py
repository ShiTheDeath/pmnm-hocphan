from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_

from . import db
from .forms import CheckoutForm
from .models import Book, Category, Order, OrderItem

bp = Blueprint("shop", __name__)


# Giỏ hàng trong session: {"<book_id>": số_lượng} 
def _cart():
    return dict(session.get("cart", {}))


def _save_cart(cart):
    session["cart"] = cart
    session.modified = True


def cart_lines():
    """Các dòng giỏ hàng; giá luôn lấy mới nhất từ CSDL, sách đã bị xoá thì bỏ khỏi giỏ."""
    cart = _cart()
    ids = [int(k) for k in cart]
    books = {b.id: b for b in Book.query.filter(Book.id.in_(ids)).all()} if ids else {}
    lines, clean = [], {}
    for key, qty in cart.items():
        book = books.get(int(key))
        if book and qty > 0:
            clean[key] = qty
            lines.append({"book": book, "qty": qty, "amount": book.price * qty})
    if clean != cart:
        _save_cart(clean)
    return lines


def shipping_fee(subtotal):
    if subtotal >= current_app.config["FREE_SHIP_FROM"]:
        return 0
    return current_app.config["SHIPPING_FEE"]


def safe_next():
    nxt = request.form.get("next", "")
    if nxt.startswith("/") and not nxt.startswith("//") and "\\" not in nxt:
        return nxt
    return url_for("shop.book_list")


# Danh sách sách 
@bp.route("/")
def index():
    return redirect(url_for("shop.book_list"))


@bp.route("/books")
def book_list():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", type=int)
    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Book.title.ilike(like), Book.author.ilike(like)))
    if cat:
        query = query.filter(Book.category_id == cat)
    books = query.order_by(Book.id.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "shop/book_list.html", books=books, categories=categories, q=q, cat=cat
    )


# ---------- ② Chọn sách ----------
@bp.route("/books/<int:book_id>")
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)
    in_cart = _cart().get(str(book_id), 0)
    return render_template(
        "shop/book_detail.html", book=book, in_cart=in_cart, max_qty=max(book.stock - in_cart, 0)
    )


@bp.post("/cart/add/<int:book_id>")
def cart_add(book_id):
    book = db.get_or_404(Book, book_id)
    back = safe_next()
    try:
        qty = int(request.form.get("quantity", "1"))
    except ValueError:
        qty = 0
    cart = _cart()
    have = cart.get(str(book_id), 0)
    room = book.stock - have

    if book.stock <= 0:
        flash(f"“{book.title}” đã hết hàng.", "danger")
    elif room <= 0:
        flash(f"Bạn đã có {have} cuốn “{book.title}” trong giỏ, bằng số hàng còn lại.", "danger")
    elif qty < 1 or qty > room:
        flash(f"Số lượng không hợp lệ: chọn từ 1 đến {room}.", "danger")
    else:
        cart[str(book_id)] = have + qty  # đã có trong giỏ thì cộng dồn
        _save_cart(cart)
        flash(f"Đã thêm {qty} × {book.title} vào giỏ hàng.", "success")
    return redirect(back)


# Giỏ hàng 
@bp.route("/cart")
def cart_view():
    lines = cart_lines()
    total = sum(l["amount"] for l in lines)
    return render_template("shop/cart.html", lines=lines, total=total)


@bp.post("/cart/increase/<int:book_id>")
def cart_increase(book_id):
    cart = _cart()
    book = db.session.get(Book, book_id)
    key = str(book_id)
    if book and key in cart:
        if cart[key] < book.stock:
            cart[key] += 1
            _save_cart(cart)
        else:
            flash(f"“{book.title}” chỉ còn {book.stock} cuốn.", "warning")
    return redirect(url_for("shop.cart_view"))


@bp.post("/cart/decrease/<int:book_id>")
def cart_decrease(book_id):
    cart = _cart()
    key = str(book_id)
    if key in cart:
        cart[key] -= 1
        if cart[key] <= 0:
            del cart[key]
        _save_cart(cart)
    return redirect(url_for("shop.cart_view"))


@bp.post("/cart/remove/<int:book_id>")
def cart_remove(book_id):
    cart = _cart()
    if cart.pop(str(book_id), None) is not None:
        _save_cart(cart)
        flash("Đã xoá sách khỏi giỏ hàng.", "info")
    return redirect(url_for("shop.cart_view"))


@bp.post("/cart/clear")
def cart_clear():
    _save_cart({})
    flash("Đã xoá toàn bộ giỏ hàng.", "info")
    return redirect(url_for("shop.cart_view"))


# Thông tin khách hàng 
@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    lines = cart_lines()
    if not lines:
        flash("Giỏ hàng trống, hãy chọn sách trước khi đặt hàng.", "warning")
        return redirect(url_for("shop.cart_view"))

    subtotal = sum(l["amount"] for l in lines)
    fee = shipping_fee(subtotal)
    form = CheckoutForm()

    if form.validate_on_submit():
        # Kiểm tra lại tồn kho và trừ kho trong cùng một giao dịch
        short = []
        for l in lines:
            res = db.session.execute(
                db.update(Book)
                .where(Book.id == l["book"].id, Book.stock >= l["qty"])
                .values(stock=Book.stock - l["qty"])
            )
            if res.rowcount == 0:
                short.append(l["book"].title)
        if short:
            db.session.rollback()
            flash("Không đủ hàng: " + ", ".join(f"“{t}”" for t in short)
                  + ". Vui lòng điều chỉnh giỏ hàng.", "danger")
            return redirect(url_for("shop.cart_view"))

        order = Order(
            customer_name=form.full_name.data.strip(),
            phone=form.phone.data.strip(),
            email=(form.email.data or "").strip() or None,
            address=form.address.data.strip(),
            note=(form.note.data or "").strip() or None,
            payment=form.payment.data,
            subtotal=subtotal,
            shipping_fee=fee,
            total=subtotal + fee,
            status="pending",
        )
        for l in lines:
            order.items.append(
                OrderItem(book_id=l["book"].id, unit_price=l["book"].price, quantity=l["qty"])
            )
        order.add_history("pending", "Đặt hàng")
        db.session.add(order)
        db.session.commit()

        _save_cart({})
        mine = session.get("my_orders", [])
        mine.append(order.id)
        session["my_orders"] = mine
        flash("Đặt hàng thành công!", "success")
        return redirect(url_for("shop.order_done", order_id=order.id))

    return render_template(
        "shop/checkout.html", form=form, lines=lines, subtotal=subtotal, fee=fee,
        total=subtotal + fee, free_from=current_app.config["FREE_SHIP_FROM"],
    )


# Đặt hàng thành công 
@bp.route("/orders/<int:order_id>")
def order_done(order_id):
    order = db.get_or_404(Order, order_id)
    if order_id not in session.get("my_orders", []):
        abort(404)  # chỉ có người vừa đặt mới xem được
    return render_template("shop/order_done.html", order=order)