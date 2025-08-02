from flask import Flask, request, render_template, jsonify
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files['file']
    if not f:
        return jsonify({'error': '파일이 없습니다.'}), 400

    # 예시: CSV에서 '이름', '나이' 열 추출 후, 나이 평균값 계산
    df = pd.read_csv(f)
    if '이름' not in df.columns or '나이' not in df.columns:
        return jsonify({'error': '이름, 나이 열이 필요합니다.'}), 400

    preview = df[['이름', '나이']].head().to_dict(orient='records')
    avg_age = df['나이'].mean()

    return jsonify({
        'preview': preview,
        'avg_age': round(avg_age, 2)
    })

if __name__ == '__main__':
    app.run(debug=True)
