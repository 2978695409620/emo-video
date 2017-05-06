import ast
import os
import requests

from apiclient.discovery import build
from apiclient.errors import HttpError
from flask import Flask, render_template, url_for, redirect, request, jsonify, flash, send_from_directory
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

DEVELOPER_KEY = os.environ.get('youtube_api_key')
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MAX_VIDEO_RESULT = 1

def search_youtube(q, maxResults):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

	search_response = youtube.search().list(
		q=q,
		part="id",
		maxResults=maxResults
	).execute()

	video_urls = []

	for search_result in search_response.get("items", []):
		if search_result["id"]["kind"] == "youtube#video":
			video_urls.append('//youtube.com/embed/' + search_result["id"]["videoId"])

	return video_urls

def validate_image(filename):
	if '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']:
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
		
		scores = result_list[0]['scores']
		for emotion, score in scores.iteritems():
			if float(score) > high_score:
				dominant_emotion = emotion
				high_score = float(score)

		video_urls = search_youtube(dominant_emotion, MAX_VIDEO_RESULT)

		return render_template('video.html', emotion=dominant_emotion, video_urls=video_urls)

	return 'No image found'

@app.route('/images/<string:filename>/')
def display_image(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run()