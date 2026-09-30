from flask import Flask, render_template, request as req, jsonify, abort
app = Flask(__name__)
BOOKS = [
    {"id": 1, "title": "Bleach", "author": "Tite Kubo", "year": 2001, "category": "Truyện tranh", "available": True},
    {"id": 2, "title": "Flask Web Development", "author": "Miguel Grinberg", "year": 2018, "category": "Lập trình", "available": False},
    {"id": 3, "title": "Naruto", "author": "Kishimoto", "year": 2000, "category": "Truyện tranh", "available": True},
    {"id": 4, "title": "Tư Duy Nhanh Và Chậm", "author": "Daniel Kahneman", "year": 2011, "category": "Kỹ năng", "available": True},
]

@app.route("/")
def index():
    total_books = len(BOOKS)
    available_books = sum(1 for b in BOOKS if b["available"])
    return render_template("index.html", total_books=total_books, available_books=available_books)

@app.route("/books")
def books_list():
    category = req.args.get("category")
    categories = sorted(list(set(b["category"] for b in BOOKS)))
    filtered_books = BOOKS
    if category:
        filtered_books = [b for b in BOOKS if b["category"] == category]       
    return render_template("books.html", books=filtered_books, categories=categories, selected_category=category)
@app.route("/books/<int:book_id>")

def book_detail(book_id):
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if not book:
        return render_template("404.html", message=f"Không có sách với ID = {book_id}"), 404
    return render_template("book_detail.html", book=book)

@app.route("/api/books")
def api_books():
    category = req.args.get("category")
    filtered_books = BOOKS 
    if category:
        filtered_books = [b for b in BOOKS if b["category"] == category]
    return jsonify(filtered_books)

@app.route("/api/books/<int:book_id>")
def api_book_detail(book_id):
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if not book:
        return jsonify({"error": f"Không có sách với ID = {book_id}"}), 404
    return jsonify(book)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", message="Lỗi 404: Trang không tồn tại"), 404
if __name__ == "__main__":
    app.run(debug=True)