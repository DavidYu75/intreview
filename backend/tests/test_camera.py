import cv2
import time

def test_camera(camera_index=1):  # Try camera 1 instead of 0
    print(f"Testing camera {camera_index}...")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("Failed to open camera!")
        return
        
    # Try to force some camera settings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_EXPOSURE, 0.5)  # Try to adjust exposure
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)  # Try to adjust brightness
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
    brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
    
    print(f"\nCamera properties:")
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"Exposure: {exposure}")
    print(f"Brightness: {brightness}")
    
    print("\nTrying to read frames...")
    print("Press 'q' to quit, 's' to save a frame")
    
    frame_count = 0
    start_time = time.time()
    
    while frame_count < 100:  # Try more frames
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame!")
            break
            
        if frame is not None:
            print(f"\rFrame {frame_count}: Shape={frame.shape}, "
                  f"Min={frame.min()}, Max={frame.max()}, "
                  f"Mean={frame.mean():.2f}", end="")
            
            # Display the frame
            cv2.imshow('Camera Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                cv2.imwrite(f'camera_test_frame_{frame_count}.jpg', frame)
                print(f"\nSaved frame {frame_count}")
            
        frame_count += 1
        
    elapsed_time = time.time() - start_time
    actual_fps = frame_count / elapsed_time
    print(f"\n\nActual FPS: {actual_fps:.2f}")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Try both cameras
    print("Testing camera 0...")
    test_camera(0)
    print("\nTesting camera 1...")
    test_camera(1)