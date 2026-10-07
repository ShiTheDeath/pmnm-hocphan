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