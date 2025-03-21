# 🚗 Automatic License Plate Recognition (ALPR) with QR Code Payment Integration

*A smart parking system with real-time license plate recognition and QR code-based payment handling.*

---

## ✅ Features

- 🔍 **License Plate Recognition**
    - Detects Indian license plates using **OpenCV** and **EasyOCR**.
    - Draws bounding boxes around detected plates in real-time.
- 💳 **QR Code Payment**
    - Generates **QR codes** for parking fee payments using **Razorpay**.
    - Auto-marks payment as successful after 20 seconds if not confirmed.
- 📊 **Data Storage & Export**
    - Stores detected license plates and payment details in **Excel** files.
    - Exports to `detected_plates.xlsx` and `paid_plates.xlsx`.
- 🎥 **Real-time Visualization**
    - Displays video frames with bounding boxes and detected plate information.

---

## ⚙️ Tech Stack

- **Programming Language:** Python  
- **Libraries:** 
    - `OpenCV` → For video frame processing  
    - `EasyOCR` → For license plate text extraction  
    - `Pandas` → For data storage and Excel export  
    - `qrcode` → For generating QR codes  
    - `Razorpay` → For payment handling  
    - `matplotlib` → For real-time frame display  

---
