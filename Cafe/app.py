import math
from flask import Flask, render_template, request as req, abort
from datetime import datetime

app = Flask(__name__)

SHOP = {"name": "Cà phê Sông Hương", "address": "12 Lê Lợi, TP. Huế", "open": 7, "close": 22}
PROMOTIONS = ["Giảm 10% cho sinh viên", "Mua 2 tặng 1 vào thứ Hai"]

MENU = [
    {"name": "Cà phê sữa", "price": 20000, "available": True},
    {"name": "Cà phê đen", "price": 15000, "available": True},
    {"name": "Trà sữa", "price": 25000, "available": False},
    {"name": "Bánh mì", "price": 10000, "available": True},
    {"name": "Nước cam", "price": 30000, "available": True},
    {"name": "Sinh tố bơ", "price": 35000, "available": True},
    {"name": "Trà đào sả vải", "price": 28000, "available": True}
]

PER_PAGE = 3  

@app.template_filter('vnd')
def format_vnd(value):
    try:
        return f"{int(value):,}đ".replace(",", ".")
    except (ValueError, TypeError):
        return value

@app.route("/")
def index():
    hour = req.args.get("gio", type=int)
    if hour is None:
        hour = datetime.now().hour
    is_open = SHOP["open"] <= hour < SHOP["close"]
    return render_template("index.html", shop=SHOP, promotions=PROMOTIONS, hour=hour, is_open=is_open)

@app.route("/menu")
def menu():
    # Lấy trang hiện tại mặc định là 1
    page = req.args.get("page", default=1, type=int)
    
    total_items = len(MENU)
    total_pages = math.ceil(total_items / PER_PAGE) if total_items > 0 else 1

    # Trả về lỗi 404 nếu số trang nhỏ hơn 1 hoặc vượt quá tổng số trang
    if page < 1 or page > total_pages:
        abort(404)

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    items = MENU[start:end]

    return render_template("menu.html", items=items, page=page, pages=total_pages)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)