from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bi-mat-cua-ban'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qlsv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# BƯỚC 3: KHAI BÁO MODEL STUDENT
# ==========================================
class Student(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    mssv: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gpa: Mapped[float] = mapped_column(default=0.0)

    def __repr__(self):
        return f"<Student {self.mssv} {self.name}>"

# Kiểu trả về văn bản thuần để trình duyệt không hiểu nhầm là HTML
TEXT = {"Content-Type": "text/plain; charset=utf-8"}

# ==========================================
# BƯỚC 5: THÊM DỮ LIỆU BẰNG VIEW FUNCTION
# ==========================================
@app.get("/them-mau")
def add_sample():
    total = db.session.scalar(db.select(func.count(Student.id)))
    if total > 0:
        return f"Đã có {total} sinh viên, không thêm nữa."

    an = Student(mssv="23T1020001", name="Nguyễn Văn An", gpa=8.5)
    
    before = an.id  # Sẽ là None vì chưa gởi xuống CSDL
    db.session.add(an)
    
    db.session.add_all([
        Student(mssv="23T1020002", name="Trần Thị Bình", gpa=6.8),
        Student(mssv="23T1020003", name="Lê Hoàng Cường", gpa=9.1),
        Student(mssv="23T1020004", name="Phạm Minh Dũng", gpa=4.5),
        Student(mssv="23T1020005", name="Hoàng Thu Hà", gpa=7.4),
    ])
    
    db.session.commit()  # Ghi thật sự xuống CSDL
    
    return (f"Đã thêm 5 sinh viên. id của An: "
            f"trước commit = {before}, "
            f"sau commit = {an.id}")

# ==========================================
# BƯỚC 6: ĐỌC DỮ LIỆU BẰNG VIEW FUNCTION
# ==========================================
@app.get("/thu-truy-van")
def try_queries():
    if db.session.scalar(db.select(func.count(Student.id))) == 0:
        return "Chưa có dữ liệu, hãy mở /them-mau trước.", 200, TEXT

    lines = []
    
    # 1 & 2. Lấy theo khóa chính (id)
    lines.append(f"1. get(3): {db.session.get(Student, 3)}")
    lines.append(f"2. get(99): {db.session.get(Student, 99)}")

    # 3. Lấy tất cả danh sách sinh viên
    everyone = db.session.execute(db.select(Student)).scalars().all()
    lines.append(f"3. Tất cả: {len(everyone)} sinh viên")

    # 4. Lọc sinh viên có GPA >= 8 và sắp xếp giảm dần
    stmt = (db.select(Student)
            .where(Student.gpa >= 8)
            .order_by(Student.gpa.desc()))
    good = db.session.execute(stmt).scalars().all()
    lines.append(f"4. Điểm >= 8: {good}")

    # 5. Lọc sinh viên theo mssv cụ thể
    binh = db.session.scalar(db.select(Student).filter_by(mssv="23T1020002"))
    lines.append(f"5. MSSV 23T1020002: {binh}")

    # 6. Thống kê tổng số lượng và điểm trung bình
    count = db.session.scalar(db.select(func.count(Student.id)))
    avg = db.session.scalar(db.select(func.avg(Student.gpa)))
    lines.append(f"6. Số SV: {count}, điểm TB: {avg:.2f}")

    return "\n".join(lines), 200, TEXT

@app.get("/danh-sach-bang")
def show_student_table():
    # 1. Truy vấn lấy tất cả sinh viên
    students = db.session.scalars(db.select(Student)).all()

    # 2. Thống kê tổng số lượng và điểm trung bình
    count = db.session.scalar(db.select(func.count(Student.id))) or 0
    avg_gpa = db.session.scalar(db.select(func.avg(Student.gpa))) or 0.0

    # 3. Trả về giao diện bảng HTML qua render_template
    return render_template(
        'students_table.html',
        students=students,
        count=count,
        avg_gpa=avg_gpa
    )

@app.get('/')
def index():
    # Lấy danh sách tất cả sinh viên
    students = db.session.scalars(db.select(Student)).all()
    
    # Tính tổng số lượng sinh viên và GPA trung bình
    count = db.session.scalar(db.select(func.count(Student.id))) or 0
    avg_gpa = db.session.scalar(db.select(func.avg(Student.gpa))) or 0.0
    
    # Trả về template kèm các dữ liệu
    return render_template(
        'students.html',
        students=students,
        count=count,
        avg_gpa=avg_gpa
    )
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tạo các bảng chưa có theo model
    app.run(debug=True)