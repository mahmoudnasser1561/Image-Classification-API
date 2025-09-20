# Flask Image Classification API
A RESTful API built with Flask and TensorFlow for image classification using the pre-trained InceptionV3 model. It features user authentication, token-based rate limiting, MongoDB for user and token management, and Docker for streamlined deployment.

## Features
* Image Classification: Classify images from URLs using TensorFlow's InceptionV3 model, returning top-5 predictions with confidence scores.

* User Authentication: Secure registration and login with bcrypt password hashing.

* Token-Based Rate Limiting: Users start with 4 tokens, consumed per classification request.

* Admin Token Refill: Admin endpoint to reset user tokens securely.

* MongoDB Integration: Stores user credentials and token counts in a MongoDB database.

* Dockerized Deployment: Uses Docker and Docker Compose for easy, reproducible setup.

## Tech Stack

* Backend: Flask, Flask-RESTful

* Machine Learning: TensorFlow, Keras (InceptionV3) wighted on ImageNet

* Database: MongoDB

* Security: bcrypt

* Deployment: Docker, Docker Compose
