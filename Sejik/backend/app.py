from flask import Flask, request, jsonify, send_file
from your_voice_code import speech_to_text, generate_response, text_to_speech  # 함수 재활용


@app.route('/api/voicechat', methods=['POST'])
def voicechat():
    # wav 파일 받기
    f = request.files['audio']
    audio_path = "input.wav"
    f.save(audio_path)

    # 음성->텍스트
    input_text = speech_to_text(audio_path)
    # AI 답변 생성
    answer_text = generate_response(input_text)
    # 답변을 음성으로
    output_audio_path = text_to_speech(answer_text)
    # 응답 (텍스트/음성파일명)
    return jsonify({'text': answer_text, 'audio': output_audio_path})
