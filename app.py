import os

import ast
from flask import Flask, render_template, url_for, redirect, request, jsonify, flash, send_from_directory
import requests
from werkzeug import secure_filename

app = Flask(__name__)
app.debug = True

app.config['UPLOAD_FOLDER'] = '/tmp/'
app.config['ALLOWED_EXTENSIONS'] = set(['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'])

SUBSCRIPTION_KEY = os.environ.get('emotion_key')
EMOTION_URL = 'https://westus.api.cognitive.microsoft.com/emotion/v1.0/recognize'

headers = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
}

def validate_image(filename):
	if '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']:
		return True
	return False

def build_image_url(filename):
	return request.url_root + 'images/' + filename

@app.route('/', methods=['GET'])
def landing():
	return render_template('upload.html')

@app.route('/video/', methods=['POST'])
def display_videos():
	picture = request.files['file']
	return picture.filename
	if picture and validate_image(picture.filename):
		filename = secure_filename(picture.filename)
		picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

		img_url = build_image_url(filename)
		body = "{'url': '%s'}" % img_url

		result = requests.post(EMOTION_URL, headers=headers, data=body)

		high_score = 0
		dominant_emotion = ''

		result_list = ast.literal_eval(result.content)

		if 'error' in result_list:
			return 'Could not process image'
		elif not result_list or len(result_list) == 0:
			return 'Invalid Image'
		else:
			scores = result_list[0]['scores']
			for emotion, score in scores.iteritems():
				if float(score) > high_score:
					dominant_emotion = emotion
					high_score = float(score)
			return render_template('video.html', emotion=dominant_emotion)

	return 'No image found'

@app.route('/images/<string:filename>/')
def display_image(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run()