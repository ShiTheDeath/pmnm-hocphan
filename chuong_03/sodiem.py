from flask import Flask, request, jsonify, url_for, redirect, abort, make_response
from markupsafe import escape

app = Flask(__name__)
app.json.ensure_ascii = False #JSON tiếng việt có dấu

STUDENTS = { 
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A",
                    "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A",
                    "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B",
                    "scores": {"PMMNM": 9.5, "CSDL": 9.0}}, 
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B",
                    "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A",
                    "scores": {}}, 
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C",
                    "scores": {"PMMNM": 7.5, "MMT": 8.0}}, 
}

#Câu 0.3
def average(scores): #Trung bình cộng
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)

def rank(avg): #Xếp loại học lực
    if avg is None:
        return "Chưa có điểm"
    if avg >= 8.5:
        return "Giỏi"
    if avg >= 7.0:
        return "Khá"
    if avg >= 5.0:
        return "Trung bình"
    return "Yếu"

def student_summary(mssv):
    if mssv not in STUDENTS:
        return None
    s = STUDENTS[mssv]
    avg = average(s["scores"])
    return {
        "mssv": mssv,
        "name": s["name"],
        "lop": s["lop"],
        "scores": s["scores"],
        "average": avg,
        "rank": rank(avg)
    }

#Câu 0.4
def layout(title, body):
    escaped_title = escape(title) 
    home_url = url_for('index') 
    students_url = url_for('student_list') 
    search_url = url_for('search_students') 
    
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{escaped_title} - Sổ điểm</title>
</head>
<body>
    <nav>
        <a href="{home_url}">Trang chủ</a> · 
        <a href="{students_url}">Sinh viên</a> · 
        <a href="{search_url}">Tìm kiếm</a>
    </nav>
    <hr>
    <h1>{escaped_title}</h1>
    {body}
</body>
</html>"""

#Câu 1
@app.route("/")
def index():
    total_students = len(STUDENTS)
    total_classes = len(set(s["lop"] for s in STUDENTS.values()))
    
    body = f"""
    <p>Tổng số sinh viên: {total_students}</p>
    <p>Số lớp: {total_classes}</p>
    <ul>
        <li><a href="{url_for('student_list')}">Xem danh sách sinh viên</a></li>
        <li><a href="{url_for('api_students')}">Xem danh sách sinh viên</a></li>
    </ul>
    """
    return layout("Trang chủ", body)

#Câu 2
@app.route("/students")
def student_list():
    filter_lop = request.args.get("lop", "").strip()
    all_classes = sorted(list(set(s["lop"] for s in STUDENTS.values())))
    # Thanh lọc lớp
    filter_links = [f'<a href="{url_for("student_list")}">Tất cả</a>']
    for c in all_classes:
        filter_links.append(f'<a href="{url_for("student_list", lop=c)}">{c}</a>')
    
    nav_html = "<p>Lọc theo lớp: " + " | ".join(filter_links) + "</p>"
    
    # Lọc danh sách sinh viên (không phân biệt hoa thường)
    filtered = []
    for mssv, info in STUDENTS.items():
        if not filter_lop or info["lop"].lower() == filter_lop.lower():
            filtered.append((mssv, info))
            
    if not filtered:
        body = nav_html + "<p>Không có sinh viên phù hợp.</p>"
        return layout("Danh sách sinh viên", body)
        
    # Dựng bảng sinh viên
    rows = []
    for mssv, info in filtered:
        summary = student_summary(mssv)
        detail_url = url_for("student_detail", mssv=mssv)
        avg_str = f"{summary['average']:.2f}" if summary["average"] is not None else "—"
        
        rows.append(f"""
        <tr>
            <td><a href="{detail_url}">{escape(mssv)}</a></td>
            <td>{escape(info['name'])}</td>
            <td>{escape(info['lop'])}</td>
            <td>{avg_str}</td>
            <td>{escape(summary['rank'])}</td>
        </tr>
        """)
        
    table_html = f"""
    <table border="1" cellpadding="5" cellspacing="0">
        <thead>
            <tr><th>MSSV</th><th>Họ tên</th><th>Lớp</th><th>Điểm TB</th><th>Xếp loại</th></tr>
        </thead>
        <tbody>
            {"".join(rows)}
        </tbody>
    </table>
    """
    return layout("Danh sách sinh viên", nav_html + table_html)

#Câu 3
@app.route("/students/<mssv>")
def student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.") #
        
    summary = student_summary(mssv)
    info = STUDENTS[mssv]
    
    class_url = url_for("student_list", lop=info["lop"])
    export_url = url_for("export_csv", mssv=mssv)
    short_url = url_for("short_student_link", mssv=mssv)
    
    scores_rows = []
    for course, score in info["scores"].items():
        scores_rows.append(f"<tr><td>{escape(course)}</td><td>{score}</td></tr>")
        
    scores_table = f"""
    <table border="1" cellpadding="5" cellspacing="0">
        <thead><tr><th>Học phần</th><th>Điểm</th></tr></thead>
        <tbody>{"".join(scores_rows) if scores_rows else '<tr><td colspan="2">Chưa có điểm học phần nào</td></tr>'}</tbody>
    </table>
    """
    
    avg_str = f"{summary['average']:.2f}" if summary["average"] is not None else "—"
    
    body = f"""
    <p><strong>MSSV:</strong> {escape(mssv)}</p>
    <p><strong>Họ tên:</strong> {escape(info['name'])}</p>
    <p><strong>Lớp:</strong> <a href="{class_url}">{escape(info['lop'])}</a></p>
    <p><strong>Điểm trung bình:</strong> {avg_str}</p>
    <p><strong>Xếp loại:</strong> {escape(summary['rank'])}</p>
    <h3>Bảng điểm chi tiết</h3>
    {scores_table}
    <br>
    <p><a href="{export_url}">Tải bảng điểm (CSV)</a> | Link rút gọn: <a href="{short_url}">{short_url}</a></p>
    """
    return layout(f"Chi tiết: {info['name']}", body)

#Câu 4 
@app.route("/sv/<mssv>")
def short_student_link(mssv):
    return redirect(url_for("student_detail", mssv=mssv), code=301)  
#Câu 5
@app.route("/students/<mssv>/export")
def export_csv(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.") #
        
    info = STUDENTS[mssv]
    csv_lines = ["hoc_phan,diem"]
    for course, score in info["scores"].items():
        csv_lines.append(f"{course},{score}")
        
    csv_content = "\n".join(csv_lines)
    response = make_response(csv_content) #
    response.headers["Content-Type"] = "text/csv; charset=utf-8" #
    response.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv" #
    return response

#Câu 6
@app.route("/search")
def search_students():
    q = request.args.get("q", "").strip()
    escaped_q = escape(q) 
    
    form_html = f"""
    <form action="{url_for('search_students')}" method="get">
        <input type="text" name="q" value="{escaped_q}" placeholder="Nhập tên hoặc MSSV...">
        <button type="submit">Tìm kiếm</button>
    </form>
    """
    if not q:
        return layout("Tìm kiếm sinh viên", form_html)
        
    results = []
    q_lower = q.lower()
    for mssv, info in STUDENTS.items():
        if q_lower in info["name"].lower() or q_lower in mssv.lower():
            results.append((mssv, info))
            
    res_html = f"<p>Tìm thấy {len(results)} kết quả cho “{escaped_q}”:</p><ul>"
    for mssv, info in results:
        detail_url = url_for("student_detail", mssv=mssv)
        res_html += f'<li><a href="{detail_url}">{escape(mssv)} - {escape(info["name"])}</a> ({escape(info["lop"])})</li>'
    res_html += "</ul>"
    return layout("Tìm kiếm sinh viên", form_html + res_html)

#Câu 7
@app.route("/api/students", methods=["GET"])
def api_students():
    lop_filter = request.args.get("lop")
    min_avg_raw = request.args.get("min_avg")
    
    min_avg = None
    if min_avg_raw is not None:
        try:
            min_avg = float(min_avg_raw)
        except ValueError:
            abort(400, description="Tham số min_avg phải là một số thực hợp lệ.")
            
    result = []
    for mssv in STUDENTS:
        summary = student_summary(mssv)
        #Lọc theo lớp (không phân biệt hoa thường)
        if lop_filter and summary["lop"].lower() != lop_filter.lower():
            continue    
        # Lọc theo min_avg (bỏ qua sinh viên chưa có điểm)
        if min_avg is not None:
            if summary["average"] is None or summary["average"] < min_avg:
                continue
                
        result.append(summary)
        
    return jsonify(result)

@app.route("/api/students/<mssv>", methods=["GET"])
def api_student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.") #
    return jsonify(student_summary(mssv))

#Câu 8
@app.route("/api/students/<mssv>/scores/<course>", methods=["GET", "PUT", "DELETE", "POST"])
def api_student_course_score(mssv, course):
    if request.method == "POST":
        abort(405, description="Phương thức POST không được hỗ trợ tại URL này.") #
        
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.") #
        
    course_upper = course.upper() # Luôn lưu dạng chữ hoa
    scores = STUDENTS[mssv]["scores"]
    
    if request.method == "GET":
        if course_upper not in scores:
            abort(404, description=f"Học phần {course_upper} chưa có điểm.") 
        return jsonify({"mssv": mssv, "course": course_upper, "score": scores[course_upper]})
        
    elif request.method == "PUT":
        score_raw = request.args.get("score")
        if score_raw is None:
            abort(400, description="Thiếu tham số score.") 
            
        try:
            score_val = float(score_raw)
        except ValueError:
            abort(400, description="Tham số score phải là số.") 
            
        if not (0.0 <= score_val <= 10.0):
            abort(400, description="Điểm phải nằm trong khoảng [0, 10].") 
            
        existed = course_upper in scores
        scores[course_upper] = score_val # Thêm hoặc sửa điểm
        
        updated_summary = student_summary(mssv)
        res_data = {
            "mssv": mssv,
            "course": course_upper,
            "score": score_val,
            "average": updated_summary["average"]
        }
        
        if not existed:
            # Thêm mới: trả về 201 kèm header Location
            res = jsonify(res_data)
            res.status_code = 201
            res.headers["Location"] = url_for("api_student_course_score", mssv=mssv, course=course_upper) #
            return res
        else:
            # Sửa điểm: trả về 200
            return jsonify(res_data), 200
            
    elif request.method == "DELETE":
        if course_upper not in scores:
            abort(404, description=f"Học phần {course_upper} chưa có điểm.") 
        del scores[course_upper]
        return "", 204 # Trả về 204 body rỗng
#Câu 9
ERR_TITLES = {
    400: "Dữ liệu không hợp lệ",
    404: "Không tìm thấy",
    405: "Phương thức không được hỗ trợ"
}

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
def handle_error(error):
    code = error.code
    title = ERR_TITLES.get(code, "Lỗi")
    description = getattr(error, "description", str(error))
    # URL bắt đầu bằng /api/ -> Trả về JSON
    if request.path.startswith("/api/"):
        return jsonify({"error": title, "detail": description}), code
        # Các URL khác -> Trả về giao diện HTML
    body = f"<p><strong>{escape(title)}</strong></p><p>{escape(description)}</p>"
    return layout(f"Lỗi {code}", body), code
if __name__ == '__main__':
    app.run(debug=True, port=8000)