# Smart Glasses for the Blind (ESP32-CAM & Python)

An IoT-based wearable smart glasses system designed to assist visually impaired individuals. The system captures images via an ESP32-CAM, processes them using Python-based OCR (Optical Character Recognition), and converts the text into audio feedback (Text-to-Speech).

## 🚀 Features
* **Image Capture:** Lightweight wireless image streaming using ESP32-CAM.
* **Text Recognition (OCR):** High-accuracy text extraction from captured images.
* **Audio Feedback (TTS):** Clear text-to-speech conversion for the user.

## 🛠️ Hardware Requirements
* ESP32-CAM Module
* FTDI Programmer (for uploading code to ESP32-CAM)
* Push Button (for triggering image capture)
* Power Source (Power bank or Li-Po battery)

## 💻 Software & Libraries
* **Firmware:** Arduino IDE (ESP32 Board Manager)
* **Backend:** Python 3.x
* **Core Libraries:** OpenCV, Requests, (Add your OCR library here, e.g., Tesseract/EasyOCR)

## 🔧 Setup Instructions
1. **Hardware Setup:** Connect the ESP32-CAM to the button and power supply according to the circuit diagram.
2. **Firmware:** Open `firmware/esp32_cam_code.ino`, update your Wi-Fi credentials, and upload it to the board.
3. **Python Backend:**
   * Navigate to `python_backend/`
   * Install dependencies: `pip install -r requirements.txt`
   * Run the main script: `python main.py`
