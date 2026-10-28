from flask import Flask, render_template, request as req

app = Flask(__name__)

def parse_number(val_str):
    if not val_str or not val_str.strip():
        return None, "Lỗi cả hai ô"
    
    clean_str = val_str.strip().replace(',', '.')
    try:
        val = float(clean_str)
        return val, None
    except ValueError:
        return None, "Vui lòng nhập vào một số."

@app.route('/', methods=['GET', 'POST'])
def index():
    a_raw = ''
    b_raw = ''
    op = '+'
    
    error_a = None
    error_b = None
    error_op = None
    result = None

    # Xử lý bằng request.form, gửi bằng POST về cùng URL
    if req.method == 'POST':
        a_raw = req.form.get('a', '')
        b_raw = req.form.get('b', '')
        op = req.form.get('op', '+')

        val_a, error_a = parse_number(a_raw)
        
        val_b, error_b = parse_number(b_raw)

        if op not in ['+', '-', '*', '/']:
            error_op = "Phép toán không hợp lệ"

        if error_a is None and error_b is None and error_op is None:
            res_num = None
            if op == '+':
                res_num = val_a + val_b
            elif op == '-':
                res_num = val_a - val_b
            elif op == '*':
                res_num = val_a * val_b
            elif op == '/':
                if val_b == 0:
                    error_b = "Không thể chia cho 0"
                else:
                    res_num = val_a / val_b

        
            if error_b is None and res_num is not None:
                def fmt(n):
                    return f"{int(n)}" if n.is_integer() else f"{n}"
                
                result = f"{fmt(val_a)} {op} {fmt(val_b)} = {fmt(res_num)}"

   
    return render_template('index.html', a=a_raw, b=b_raw,op=op, error_a=error_a, error_b=error_b,
        error_op=error_op,
        result=result
    )

if __name__ == '__main__':
    app.run(debug=True)