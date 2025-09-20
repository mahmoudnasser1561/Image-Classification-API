from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import numpy as np
import requests
import os
import pymongo

from keras.applications import InceptionV3
from keras.applications.inception_v3 import preprocess_input
from keras.applications import imagenet_utils
from tensorflow.keras.utils import img_to_array
from PIL import Image
from io import BytesIO

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['CUDA_VISIBLE_DEVICES'] = ''

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017", serverSelectionTimeoutMS=5000)
db = client.ImageRevognition
users = db["Users"]

def verify_pw(user_name, password):
    if not user_exists(user_name):
        return False
    hashed_pw = users.find({"Username": user_name})[0]["Password"]
    return bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw

def user_exists(username):
    return users.count_documents({"Username": username}) > 0

def generate_return_dict(status, msg):
    return {"status": status, "msg": msg}

def verify_credentials(user_name, password):
    if not user_exists(user_name):
        return generate_return_dict(301, "Invalid Username"), True
    if not verify_pw(user_name, password):
        return generate_return_dict(302, "Incorrect Password"), True
    return None, False

class Register(Resource):
    def post(self):
        posted_data = request.get_json()
        user_name = posted_data["username"]
        password = posted_data["password"]

        if user_exists(user_name):
            return jsonify(generate_return_dict(301, "Invalid username, user already exists"))
        
        hashed_passwd = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        users.insert_one({
            "Username": user_name,
            "Password": hashed_passwd,
            "Tokens": 4
        })
        return jsonify(generate_return_dict(200, "You have successfully signed up for the API"))

class Classify(Resource):
    model = None

    def __init__(self):
        if Classify.model is None:
            Classify.model = InceptionV3(weights="imagenet")

    def post(self):
        posted_data = request.get_json()
        user_name = posted_data["username"]
        password = posted_data["password"]
        url = posted_data["url"]

        ret_json, error = verify_credentials(user_name, password)
        if error:
            return jsonify(ret_json)
        
        tokens = users.find({"Username": user_name})[0]["Tokens"]
        if tokens <= 0:
            return jsonify(generate_return_dict(303, "Not Enough Tokens"))
        
        if not url:
            return jsonify(generate_return_dict(400, "No URL provided"))
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
        except (requests.RequestException, IOError) as e:
            return jsonify(generate_return_dict(400, f"Failed to load image: {str(e)}"))
        
        if img.format not in ['JPEG', 'PNG']:
            return jsonify(generate_return_dict(400, "Unsupported image format"))
       
        img = img.resize((299, 299))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        prediction = Classify.model.predict(img_array)
        actual_prediction = imagenet_utils.decode_predictions(prediction, top=5)

        ret_json = {
            "status": 200,
            "predictions": {pred[1]: float(pred[2] * 100) for pred in actual_prediction[0]}
        }

        users.update_one(
            {"Username": user_name},
            {"$set": {"Tokens": tokens - 1}}
        )

        return jsonify(ret_json)

class Refill(Resource):
    def post(self):
        posted_data = request.get_json()
        user_name = posted_data["username"]
        password = posted_data["admin_pw"]
        try:
            amount = int(posted_data["amount"])
            if amount <= 0:
                return jsonify(generate_return_dict(400, "Amount must be positive"))
        except (KeyError, ValueError):
            return jsonify(generate_return_dict(400, "Invalid or missing amount"))

        if not user_exists(user_name):
            return jsonify(generate_return_dict(301, "Invalid Username"))
        
        correct_pass = "abc123"
        if password != correct_pass:
            return jsonify(generate_return_dict(302, "Incorrect Password"))
        
        users.update_one(
            {"Username": user_name},
            {"$set": {"Tokens": amount}}
        )

        return jsonify(generate_return_dict(200, "Refilled"))

api.add_resource(Register, '/register')
api.add_resource(Classify, '/classify')
api.add_resource(Refill, '/refill')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)