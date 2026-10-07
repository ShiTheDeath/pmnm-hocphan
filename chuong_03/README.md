# BÀI TẬP TỔNG HỢP CHƯƠNG 3 - SỔ ĐIỂM LỚP HỌC
## 1. Kết quả `flask --app sodiem routes`
Endpoint                  Methods                   Rule
------------------------- ------------------------- ----------------------------------
api_student_course_score  DELETE, GET, POST, PUT    /api/students/<mssv>/scores/<course>
api_student_detail        GET                       /api/students/<mssv>
api_students              GET                       /api/students
export_csv                GET                       /students/<mssv>/export
index                     GET                       /
search_students           GET                       /search
short_student_link        GET                       /sv/<mssv>
static                    GET                       /static/<path:filename>
student_detail            GET                       /students/<mssv>
student_list              GET                       /students

## 2. Kết quả kiểm thử curl
- `curl -i http://127.0.0.1:8000/sv/23T1020001`: 
HTTP/1.1 301 MOVED PERMANENTLY
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:05:36 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 227
Location: /students/23T1020001
Connection: close
- `curl -i http://127.0.0.1:8000/students/23T1020001/export`: 
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:05:46 GMT
Content-Type: text/csv; charset=utf-8
Content-Length: 40
Content-Disposition: attachment; filename=diem_23T1020001.csv
Connection: close

hoc_phan,diem
PMMNM,8.5
CSDL,7.0
MMT,9.0
- `curl "$B/api/students?lop=k47a&min_avg=7"`: 
[
  {
    "average": 8.17,
    "lop": "K47A",
    "mssv": "23T1020001",
    "name": "Nguyễn Văn An",
    "rank": "Khá",
    "scores": {
      "CSDL": 7.0,
      "MMT": 9.0,
      "PMMNM": 8.5
    }
  }
]
- `curl -i "$B/api/students?min_avg=abc"`: 
HTTP/1.1 400 BAD REQUEST
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:11:59 GMT
Content-Type: application/json
Content-Length: 121
Connection: close

{
  "detail": "Tham số min_avg phải là một số thực hợp lệ.",
  "error": "Dữ liệu không hợp lệ"
}
- `curl -i $B/api/students/999`: 
HTTP/1.1 404 NOT FOUND
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:12:05 GMT
Content-Type: application/json
Content-Length: 91
Connection: close

{
  "detail": "Không có sinh viên với MSSV = 999.",
  "error": "Không tìm thấy"
}
- `curl -i -X PUT "$S/web?score=9"`:
HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:12:21 GMT
Content-Type: application/json
Content-Length: 80
Location: /api/students/23T1020005/scores/WEB
Connection: close

{
  "average": 9.0,
  "course": "WEB",
  "mssv": "23T1020005",
  "score": 9.0
}
- `curl -X PUT "$S/WEB?score=7.5"`: 
{
  "average": 7.5,
  "course": "WEB",
  "mssv": "23T1020005",
  "score": 7.5
}
- `curl -i -X PUT "$S/WEB?score=11"`: 
HTTP/1.1 400 BAD REQUEST
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:12:34 GMT
Content-Type: application/json
Content-Length: 107
Connection: close

{
  "detail": "Điểm phải nằm trong khoảng [0, 10].",
  "error": "Dữ liệu không hợp lệ"
}
- `curl -i -X DELETE $S/WEB`: 
HTTP/1.1 204 NO CONTENT
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:12:39 GMT
Content-Type: text/html; charset=utf-8
Connection: close
- `curl -i -X POST $S/WEB`: 
HTTP/1.1 405 METHOD NOT ALLOWED
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:12:43 GMT
Content-Type: application/json
Content-Length: 139
Connection: close

{
  "detail": "Phương thức POST không được hỗ trợ tại URL này.",
  "error": "Phương thức không được hỗ trợ"
}
- `curl -i -X POST $B/students`: 
Server: Werkzeug/3.1.9 Python/3.13.15
Date: Wed, 07 Oct 2026 14:12:46 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 449
Connection: close
Trả về HTML
## 3. Trả lời câu hỏi ngắn
1. **Vì sao Câu 4 dùng 301 còn Câu 8 trả 201 kèm Location?**
   - **Câu 4** sử dụng mã trạng thái `301 Moved Permanently` vì URL `/sv/<mssv>` đóng vai trò là một liên kết rút gọn cố định, giúp chuyển hướng vĩnh viễn trình duyệt/client sang URL chuẩn `/students/<mssv>`.
   - **Câu 8** trả về mã `201 Created` kèm header `Location` khi thêm mới điểm một học phần vì đây là chuẩn mực RESTful API, báo hiệu một tài nguyên điểm học phần mới vừa được tạo thành công và cung cấp URI chính xác để truy cập tài nguyên đó.

2. **Thêm điểm cho 23T1020005 rồi khởi động lại server, điểm đó còn không? Vì sao?**
   - Điểm đó **không còn**.
   - **Vì:** Dữ liệu sinh viên hiện tại chỉ được lưu trữ tạm thời trên bộ nhớ trong (biến Python `STUDENTS` thuộc bộ nhớ RAM). Khi máy chủ khởi động lại, chương trình sẽ chạy lại từ đầu và khởi tạo lại dictionary `STUDENTS` về giá trị mặc định ban đầu trong file nguồn `sodiem.py`.