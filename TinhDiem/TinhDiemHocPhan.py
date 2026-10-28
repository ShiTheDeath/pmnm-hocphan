from flask import Flask, render_template, request as req

app = Flask(__name__)

# hàm kiểm tra dùng chung cho cả 3 ô (CC, GK, CK)
def validate_score(val_str, field_label):
    if not val_str or not val_str.strip():
        return None, f"Lỗi ô {field_label}: Vui lòng nhập điểm."
    
    # Chấp nhận dấu phẩy thập phân (chuyển ',' thành '.')
    clean_str = val_str.strip().replace(',', '.')
    try:
        val = float(clean_str)
    except ValueError:
        return None, f"Lỗi ô {field_label}: Vui lòng nhập một số."
    
    # Kiểm tra điểm từ 0 đến 10
    if val < 0 or val > 10:
        return None, f"Lỗi ô {field_label}: Điểm phải từ 0 đến 10."
        
    return val, None

@app.route('/', methods=['GET', 'POST'])
def index():
    cc_raw = ''
    gk_raw = ''
    ck_raw = ''
    
    errors = {}
    result = None

    if req.method == 'POST':
        cc_raw = req.form.get('cc', '')
        gk_raw = req.form.get('gk', '')
        ck_raw = req.form.get('ck', '')

        # Sử dụng chung 1 hàm kiểm tra cho từng ô
        cc_val, err_cc = validate_score(cc_raw, "CC")
        gk_val, err_gk = validate_score(gk_raw, "GK")
        ck_val, err_ck = validate_score(ck_raw, "CK")

        if err_cc: errors['cc'] = err_cc
        if err_gk: errors['gk'] = err_gk
        if err_ck: errors['ck'] = err_ck

        if not errors:
    
            final_score = round(cc_val * 0.10 + gk_val * 0.30 + ck_val * 0.60, 1) 
            
            if ck_val < 1.0:
                letter_grade = "F (điểm thi dưới 1)"
            else:
                if final_score >= 8.5:
                    letter_grade = "A"
                elif final_score >= 7.0:
                    letter_grade = "B"
                elif final_score >= 5.5:
                    letter_grade = "C"
                elif final_score >= 4.0:
                    letter_grade = "D"
                else:
                    letter_grade = "F"

            result = f"{final_score} - {letter_grade}"

    return render_template(
        'index.html',
        cc=cc_raw,
        gk=gk_raw,
        ck=ck_raw,
        errors=errors,
        result=result
    )

if __name__ == '__main__':
    app.run(debug=True)