# Intelligent Proctor

Intelligent Proctor is a real-time computer vision app that monitors behavior through your webcam. It has two modes: Proctor and Deep Work.

**Proctor mode** is designed for exam or test environments. It watches for cheating-related items in the frame, specifically an extra person in the background, a book, a phone, or a student gazing off from the screen(for more than 2 secs). Each detected item is flagged as a violation.

**Deep Work mode** is for focus sessions. It tracks whether you are looking away from the screen and whether a phone is visible. It gives you a live focus score that updates in real time based on how distracted you are, along with a running tally of distractions as they happen.

At the end of any session, the app shows a breakdown of every violation or distraction that was detected, along with how many frames each one appeared in. In Deep Work mode, you also get a focus graph showing how your focus held up over the course of the session.

## Model

The detection runs on a YOLOv8s model fine-tuned on a custom dataset of around 110,000 images.

Dataset: https://universe.roboflow.com/maanavs-workspace/proctor_vision/dataset/1

| Split | Images |
|-------|--------|
| Train | 10,626 (92%) |
| Valid | 447 (4%) |
| Test  | 473 (4%) |

## Tech Stack

- Backend: FastAPI + WebSockets
- Frontend: React 19 + TypeScript (Vite)
- Computer Vision: OpenCV + MediaPipe + Ultralytics YOLOv8

## Running Locally

You need Python 3.10+ and Node.js installed.

**1. Start the backend**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend will be running at `http://localhost:8000`.

**2. Start the frontend**

Open a new terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

Make sure the backend is running before you open the app, as it connects over WebSocket on load.
