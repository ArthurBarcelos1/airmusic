# Air Music

Interactive musical application using camera, computer vision and real-time sound synthesis.

---

# Requirements

- Windows 10/11
- Webcam
- [Python 3.11.9](https://www.python.org/downloads/release/python-3119/)

---

# Installation

## 1. Install Python 3.11.9

Download:

[Python 3.11.9](https://www.python.org/downloads/release/python-3119/)

IMPORTANT:  
During installation, enable:

```text
Add Python to PATH
```

---

## 2. Download the project

```bash
git clone https://github.com/USERNAME/airmusic.git
```

Or download ZIP directly from GitHub.

---

## 3. Open terminal inside project folder

Example:

```bash
cd airmusic
```

---

## 4. Install dependencies

Run on PowerShell / terminal:

```bash
pip install opencv-python mediapipe numpy sounddevice
```

---

# Running

Run:

```bash
python main.py
```

---

# Controls

- Move your index finger over the left wheel to play notes
- Move your index finger over the right wheel to change harmonies
- Supports both hands simultaneously
- Press `ESC` to close

---

# Libraries Used

- OpenCV
- MediaPipe
- NumPy
- SoundDevice

---

# Features

- Real-time hand tracking
- Harmonic wheel
- Chord generation
- Continuous audio synthesis
- Transparent UI
- Musical interaction using gestures
