import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

app = Flask(__name__)

load_dotenv()
ibm_cloud_url = os.environ['IBM_CLOUD_URL']
project_id = os.environ['PROJECT_ID']
api_key = os.environ['API_KEY']

creds = {
    "url": ibm_cloud_url,
    "apikey": api_key
}

# 모델 인스턴스 준비
model = Model(
    model_id='ibm/granite-3-3-8b-instruct',
    credentials=creds,
    project_id=project_id
)

def get_completion(prompt: str) -> str:
    try:
        response = model.generate(
            prompt=prompt,
            params={
                GenParams.MAX_NEW_TOKENS: 500,
                GenParams.TEMPERATURE: 0.7
            }
        )
        return response['results'][0]['generated_text']
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': '메시지를 입력해주세요.'}), 400
        
        # 프롬프트 구성
        prompt = f"""
        You are a helpful AI assistant. Please respond to the following message in a friendly and informative way:
        
        User: {user_message}
        
        Assistant:"""
        
        # AI 응답 생성
        ai_response = get_completion(prompt)
        
        return jsonify({
            'response': ai_response,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'서버 오류가 발생했습니다: {str(e)}',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
