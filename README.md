---
title: Intelligent Proctor
emoji: 👁️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Intelligent Proctor Backend

This repository contains the backend for the Intelligent Proctor application, hosted via Hugging Face Spaces (Docker).

- **Framework:** FastAPI
- **Model:** YOLOv8 (best.pt)
- **Computer Vision:** OpenCV + MediaPipe

The web application securely connects to this backend via secure WebSockets to process frames in real-time.

## Running locally

### 1. Backend
Navigate to the `backend` directory, install requirements, and run the FastAPI server:
```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
This will start the backend on `http://localhost:8000`.

### 2. Frontend
Open a new terminal, navigate to the `frontend` directory, install dependencies, and start the development server:
```powershell
cd frontend
npm install
npm run dev
```

Remember to copy `.env.example` to `.env` in the frontend directory to ensure the `VITE_API_URL` correctly targets your local backend.
