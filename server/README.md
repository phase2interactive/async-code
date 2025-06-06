# Flask Web App

A simple Flask web application with ping API and CORS support.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

The app will run on `http://localhost:5000`

## API Endpoints

- **GET /**: Root endpoint with app info
- **GET /ping**: Health check endpoint that returns "pong"

## Features

- CORS enabled for all routes
- JSON responses
- Health check endpoint
- Development server with debug mode 