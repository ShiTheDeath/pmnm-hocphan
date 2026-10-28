from flask import Flask, render_template, request as req

app = Flask(__name__)

def parse_height(height_str):
    if not height_str or not height_str.strip():
        return None, "Vui lòng nhập chiều cao"
    
    clean_str = height_str.strip().replace(',', '.')
    try:
        val = float(clean_str)
    except ValueError:
        return None, "Lỗi ô chiều cao: Vui lòng nhập một số."
    

    if val < 50 or val > 250:
        return None, "Lỗi ô chiều cao: Giá trị phải từ 50 đến 250 (nhập mét thay vì cm)."
        
    return val, None

def parse_weight(weight_str):
    if not weight_str or not weight_str.strip():
        return None, "Vui lòng nhập cân nặng"
    
    # Chấp nhận dấu phẩy thập phân
    clean_str = weight_str.strip().replace(',', '.')
    try:
        val = float(clean_str)
    except ValueError:
        return None, "Lỗi ô cân nặng: Vui lòng nhập một số."
    
    # Cân nặng từ 10 đến 300 kg
    if val < 10 or val > 300:
        return None, "Lỗi ô cân nặng: Giá trị phải từ 10 đến 300."
        
    return val, None

@app.route('/', methods=['GET', 'POST'])
def index():
    height_raw = ''
    weight_raw = ''
    
    error_height = None
    error_weight = None
    
    bmi = None
    category = None
    color_type = None  # 'green', 'yellow', 'red'
                       # green: bình thường, yellow: thiếu cân hoặc thừa cân, red: béo phì
    ideal_weight_str = None

    if req.method == 'POST':
        height_raw = req.form.get('height', '')
        weight_raw = req.form.get('weight', '')

        # Kiểm tra và lấy giá trị chiều cao, cân nặng
        val_h, error_height = parse_height(height_raw)
        val_w, error_weight = parse_weight(weight_raw)


        if error_height is None and error_weight is None:
            # Chuyển chiều cao cm sang m
            height_m = val_h / 100.0
            
            # BMI = cân nặng / (chiều cao m)^2 (làm tròn 1 chữ số)
            bmi_val = val_w / (height_m ** 2)
            bmi = round(bmi_val, 1)

            # Cân nặng nên có ứng với BMI từ 18.5 đến 22.9
            min_ideal = round(18.5 * (height_m ** 2), 1)
            max_ideal = round(22.9 * (height_m ** 2), 1)
            ideal_weight_str = f"{min_ideal} – {max_ideal} kg"

            # Phân loại theo chuẩn người Châu Á 
            if bmi < 18.5:
                category = "Thiếu cân"
                color_type = "yellow" 
            elif bmi < 23.0:
                category = "Bình thường"
                color_type = "green"  
            elif bmi < 25.0:
                category = "Thừa cân"
                color_type = "yellow" 
            else:
                category = "Béo phì"
                color_type = "red"    

    return render_template(
        'index.html',
        height=height_raw,
        weight=weight_raw,
        error_height=error_height,
        error_weight=error_weight,
        bmi=bmi,
        category=category,
        color_type=color_type,
        ideal_weight_str=ideal_weight_str
    )

if __name__ == '__main__':
    app.run(debug=True)