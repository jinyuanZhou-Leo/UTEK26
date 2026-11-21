import cv2

def open_cam():
    # Reference: https://opencv.org/reading-and-writing-videos-using-opencv/
    cap = cv2.VideoCapture(0) # webcam usually have a index of 0

    # check if the webcam is opened successfully
    if not cap.isOpened():
        print("Error: cannot open webcam")
        raise RuntimeError
    else:
        print("INFO: Webcam is successfully connected")
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)    
    
    return cap
        

def convert_bgr2rgb(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # tranform the color space from BGR to RGB