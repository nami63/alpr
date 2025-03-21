import cv2
import easyocr
import re
import numpy as np
import pandas as pd
import qrcode
import razorpay
from datetime import datetime
from matplotlib import pyplot as plt
import time
import threading

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Razorpay Configuration
razorpay_client = razorpay.Client(auth=("rzp_test_erg9zlc2tIPljK", "XpaSN7bAdQhvsiAET12CTIKz"))

# Improved Indian license plate regex pattern
indian_plate_pattern = r'^[A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,2}\s*\d{4}$'

# Data storage
plate_data = pd.DataFrame(columns=['Plate', 'Entry_Timestamp'])
paid_plates = pd.DataFrame(columns=['Plate', 'Entry_Timestamp', 'Exit_Timestamp', 'Amount'])

# Video file path
video_path = r"C:\Users\hp\Downloads\mian project.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

frame_count = 0
plt.figure(figsize=(12, 8))
payment_done = False
qr_display_start_time = None
current_order_id = None
waiting_for_payment = False

def auto_mark_payment():
    global payment_done, waiting_for_payment, qr_display_start_time
    
    # Wait for 20 seconds
    time.sleep(10)
    
    if waiting_for_payment:
        print("✅ Auto-marking payment as successful after 20 seconds")
        payment_done = True
        waiting_for_payment = False

def generate_qr_code(amount, plate_number):
    global qr_display_start_time, waiting_for_payment
    
    order_data = {
        "amount": int(amount * 100),
        "currency": "INR",
        "receipt": f"txn_{plate_number}_{int(time.time())}"
    }

    # Create Order
    order = razorpay_client.order.create(data=order_data)
    order_id = order['id']

    # Generate QR Code
    qr_data = f"upi://pay?pa=riyashajim@oksbi&pn=SmartParking&am={amount:.2f}&cu=INR&tid={order_id}"
    qr = qrcode.make(qr_data)
    qr.show()
    
    qr_display_start_time = time.time()
    waiting_for_payment = True
    
    # Start a timer to auto-mark payment after 20 seconds
    payment_timer = threading.Thread(target=auto_mark_payment)
    payment_timer.daemon = True
    payment_timer.start()

    return order_id

def confirm_payment(order_id):
    try:
        # For test API, attempt to check actual payment
        payments = razorpay_client.payment.all({"order_id": order_id})
        for payment in payments['items']:
            if payment['status'] == 'captured':
                print("✅ Payment Successful!")
                return True
                
        # Check if we should auto-mark as paid
        global waiting_for_payment, qr_display_start_time
        if waiting_for_payment and (time.time() - qr_display_start_time >= 20):
            print("✅ Auto-marked as paid after 20 seconds")
            waiting_for_payment = False
            return True
            
        print("❗ Payment Pending...")
        return False
    except Exception as e:
        print(f"Error confirming payment: {e}")
        return False

def save_to_excel():
    plate_data.to_excel("detected_plates.xlsx", index=False)
    paid_plates.to_excel("paid_plates.xlsx", index=False)

while True:
    ret, frame = cap.read()
    if not ret or payment_done:
        print("End of video or payment completed.")
        break

    if frame_count % 5 == 0:  # Process every 5th frame for efficiency
        results = reader.readtext(frame)
        
        for (bbox, text, prob) in results:
            clean_text = ''.join(text.split()).upper()

            if re.match(indian_plate_pattern, clean_text):
                print(f"Detected Indian Plate: {clean_text} (Confidence: {prob:.2f})")

                # Draw bounding box
                (top_left, top_right, bottom_right, bottom_left) = bbox
                top_left = tuple(map(int, top_left))
                bottom_right = tuple(map(int, bottom_right))
                cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
                cv2.putText(frame, f"{clean_text} ({prob:.2f})",
                            (top_left[0], top_left[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                # Timestamp logic
                current_time = datetime.now()
                if clean_text in plate_data['Plate'].values:
                    last_time = pd.to_datetime(plate_data[plate_data['Plate'] == clean_text]['Entry_Timestamp'].values[-1])
                    time_diff = (current_time - last_time).total_seconds()
                    if time_diff > 15:
                        amount = 0.1 * (time_diff - 14)
                        print(f"QR Code Generated for ₹{amount:.2f}")
                        order_id = generate_qr_code(amount, clean_text)
                        current_order_id = order_id
                        
                        # Check payment immediately (will be checked again in main loop)
                        if confirm_payment(order_id):
                            new_paid_entry = pd.DataFrame({
                                'Plate': [clean_text],
                                'Entry_Timestamp': [last_time],
                                'Exit_Timestamp': [current_time],
                                'Amount': [amount]
                            })
                            paid_plates = pd.concat([paid_plates, new_paid_entry], ignore_index=True)
                            save_to_excel()
                            payment_done = True
                else:
                    new_entry = pd.DataFrame({'Plate': [clean_text], 'Entry_Timestamp': [current_time]})
                    plate_data = pd.concat([plate_data, new_entry], ignore_index=True)
                    save_to_excel()

    # Check for payment completion if waiting
    if waiting_for_payment and current_order_id:
        if confirm_payment(current_order_id):
            # Payment was successful (either real or auto-marked)
            clean_text = plate_data['Plate'].values[-1]
            last_time = pd.to_datetime(plate_data[plate_data['Plate'] == clean_text]['Entry_Timestamp'].values[-1])
            current_time = datetime.now()
            time_diff = (current_time - last_time).total_seconds()
            amount = 0.1 * (time_diff - 14)
            
            new_paid_entry = pd.DataFrame({
                'Plate': [clean_text],
                'Entry_Timestamp': [last_time],
                'Exit_Timestamp': [current_time],
                'Amount': [amount]
            })
            paid_plates = pd.concat([paid_plates, new_paid_entry], ignore_index=True)
            save_to_excel()
            payment_done = True

    # Display frame for visualization
    if frame_count % 30 == 0:
        plt.clf()
        plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        plt.axis('off')
        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)

    frame_count += 1

cap.release()
plt.close()
print("Video processing complete.")