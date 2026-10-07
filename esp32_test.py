import cv2
URL = 'http://10.194.84.7:81/stream'
print('Opening ESP32-CAM stream...')
cap = cv2.VideoCapture(URL)
if not cap.isOpened():
    print('ERROR: Could not open ESP32-CAM stream')
    raise SystemExit(1)
print('SUCCESS: ESP32-CAM stream opened')
print('Press Q to quit')
while True:
    ret, frame = cap.read()
    if not ret:
        print('ERROR: Frame read failed')
        break
    cv2.imshow('ESP32-CAM', frame)
    if cv2.waitKey(1) & 255 == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
print('Test finished')
