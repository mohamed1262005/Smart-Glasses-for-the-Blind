import os
import cv2
import numpy as np
import threading
import queue
import pyttsx3
import time
from ultralytics import YOLO
import pygame
from flask import Flask, request

# منع تجمد نافذة OpenCV على أنظمة ويندوز
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

app = Flask(__name__)

# تحميل نموذج YOLOv8 الخفيف والمناسب للسرعة
model = YOLO('yolov8n.pt') 

CACHE_DIR = "voice_cache"
if not os.path.exists(CACHE_DIR): 
    os.makedirs(CACHE_DIR)

# تهيئة نظام تشغيل الصوتيات
pygame.mixer.init()
sound_queue = queue.Queue(maxsize=1)

def speech_worker():
    """خيط معالجة نطق الأصوات لضمان استقرار السيرفر ومنع الـ Crashes"""
    # تهيئة محرك النطق داخل الخيط نفسه لضمان التوافقية مع الـ Multi-threading
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    
    while True:
        item = sound_queue.get()
        if item:
            file_path = f"{CACHE_DIR}/{item}.mp3"
            try:
                # تشغيل الصوت من الكاش مباشرة إن وُجد لتوفير المعالجة والوقت
                if os.path.exists(file_path):
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy(): 
                        time.sleep(0.05)
                else:
                    # تحويل النص إلى صوت وحفظه كملف مؤقت
                    engine.save_to_file(f"I see a {item}", file_path)
                    engine.runAndWait()
                    
                    # تشغيل الملف الجديد
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy(): 
                        time.sleep(0.05)
            except Exception as e:
                print(f"Audio Error: {e}")
        sound_queue.task_done()

# تشغيل خيط معالجة الصوت في الخلفية
threading.Thread(target=speech_worker, daemon=True).start()

# متغيرات منطق النطق الصوتي لمنع التكرار المزعج
last_spoken = ""
last_time = 0

# متغيرات تخزين وحماية الفريمات المتبادلة بين السيرفر ونافذة العرض
current_frame = None
frame_lock = threading.Lock()

@app.route('/upload', methods=['POST'])
def upload():
    global last_spoken, last_time, current_frame
    try:
        # استقبال البيانات الخام (Raw Bytes) من الـ ESP32-CAM وتحويلها لـ numpy array
        nparr = np.frombuffer(request.data, np.uint8)
        
        # إعادة تشكيل المصفوفة لتصبح بالأبعاد الأصلية لـ QVGA Grayscale (240 صف و 320 عمود)
        img_gray = nparr.reshape((240, 320))
        
        # تحويل الصورة إلى RGB لأن نموذج YOLO مدرب على صور ملونة بـ 3 قنوات
        img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)

        # الكشف عن الأجسام بواسطة YOLOv8
        results = model.predict(img, conf=0.5, imgsz=160, verbose=False)
        
        # منطق النطق الذكي بفاصل زمني مناسب
        if len(results[0].boxes) > 0:
            current = model.names[int(results[0].boxes.cls[0])]
            now = time.time()
            if current != last_spoken or (now - last_time > 3):
                if sound_queue.empty():
                    sound_queue.put(current)
                    last_spoken = current
                    last_time = now

        # رسم الإطارات والأسماء المكتشفة على الصورة
        annotated = results[0].plot()

        # حفظ الفريم الحالي بأمان ومشاركته مع خيط العرض
        with frame_lock:
            current_frame = annotated
        
        return "OK", 200
    except Exception as e:
        print(f"Upload Error: {e}")
        return "Error", 500

def display_worker():
    """خيط معزول لعرض نافذة الكاميرا باستقرار وسلاسة دون تهنيج"""
    global current_frame
    cv2.namedWindow("Smart Glasses Live Feed", cv2.WINDOW_AUTOSIZE)
    
    # فريم افتراضي يظهر للمستخدم في بداية التشغيل لحين استلام أول صورة
    placeholder = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.putText(placeholder, "Waiting for Camera...", (30, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    while True:
        with frame_lock:
            frame_to_show = current_frame if current_frame is not None else placeholder
        
        cv2.imshow("Smart Glasses Live Feed", frame_to_show)
        
        # إنهاء الاسكريبت وإغلاق النوافذ عند الضغط على زر 'q'
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    # تشغيل خيط النافذة الرسومية
    threading.Thread(target=display_worker, daemon=True).start()
    
    # تشغيل سيرفر الويب لاستقبال الفريمات على الشبكة المحلية
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)