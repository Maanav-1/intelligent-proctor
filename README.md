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
