import os
import tempfile
from flask import Flask, request, jsonify, send_file
import speech_recognition as sr
import pyttsx3
from pydub import AudioSegment
import re

app = Flask(__name__)

def evaluate_math_expression(expression):
    # Remove non-mathematical characters
    if "x" in expression:
        expression = expression.replace('x', '*')
    if "multiply" in expression:
        expression = expression.replace('multiply', '*')
    if "to the power of" in expression:
        expression = expression.replace('to the power of', '**')
    if "substract" in expression:
        expression = expression.replace('substract', '-')

    expression = re.sub(r'[^\d+\-*/().]', '', expression)

    try:
        result = eval(expression)
        return result
    except Exception as e:
        return str(e)

def set_female_voice():
    engine = pyttsx3.init()

    # Set the voice ID for a female voice (change the voice ID based on your system)
    female_voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens\MSTTS_V110_taIN_Kala"

    engine.setProperty('voice', female_voice_id)
    return engine

def speak_text(text, output_file):
    engine = set_female_voice()
    engine.save_to_file(text, output_file)
    engine.runAndWait()

@app.route('/process_audio', methods=['POST'])
def process_voice():
    if 'voice' not in request.files:
        return jsonify({'error': 'No file part'})
    
    voice_file = request.files['voice']

    if voice_file:
        
        audio = AudioSegment.from_file(voice_file)
        output_wav_path = "output_file.wav"
        audio.export(output_wav_path, format="wav")

        # Check if the saved file exists
        if not os.path.exists(output_wav_path):
            return jsonify({'error': 'File not saved properly'})

        recognizer = sr.Recognizer()

        try:
            with sr.AudioFile(output_wav_path) as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.record(source)

            text = recognizer.recognize_google(audio)
            
            result = evaluate_math_expression(text)

            if result is not None:
                response_text = "The result of the calculation is: " + str(result)
            else:
                response_text = "Sorry, an error occurred during the calculation."

            # Create a temporary WAV file to store the audio response
            voice_clip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            speak_text(response_text, voice_clip_path)

            # Remove the original uploaded voice file
            os.remove(output_wav_path)

            # Check if the generated audio file exists and has a non-zero size
            if os.path.exists(voice_clip_path) and os.path.getsize(voice_clip_path) > 0:
                # Send the generated audio file as a response
                return send_file(voice_clip_path, mimetype='audio/wav')
            else:
                return jsonify({'error': 'Audio file generation failed'})

        except Exception as e:
            os.remove(output_wav_path)
            return str(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
