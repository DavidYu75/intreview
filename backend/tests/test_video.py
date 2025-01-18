import sys
import os
import asyncio
import cv2
import numpy as np
import time

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.video_processor import VideoProcessor

async def test_video_processing():
    """Test video processing with webcam or sample video"""
    print("\n=== Testing Video Processing ===")
    processor = VideoProcessor()
    
    try:
        cap = cv2.VideoCapture(1)
        
        if not cap.isOpened():
            raise Exception("Could not open video source")
            
        # Get and print camera properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        print(f"\nCamera Properties:")
        print(f"Resolution: {frame_width}x{frame_height}")
        print(f"FPS: {fps}")
            
        # Wait a bit for the camera to initialize
        print("\nInitializing camera...")
        time.sleep(2)
        
        frames = []  # Store the last 30 frames for analysis
        frame_count = 0
        last_analysis_time = time.time()
        analysis_interval = 5  # Analyze metrics every 5 seconds
        
        print("\nStarting continuous video processing...")
        print("Press 'q' to stop the test")
        print("Press 's' to save the current frame")
        
        while True:
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                print("\nFailed to capture frame")
                continue
                
            try:
                # Process single frame
                processed_frame, metrics = await processor.process_frame(frame)
                
                # Keep only the last 30 frames
                frames.append(frame)
                if len(frames) > 30:
                    frames.pop(0)
                
                # Get and display real-time feedback
                feedback = await processor.get_realtime_feedback(frame)
                
                # Add frame counter and feedback to the display
                debug_info = f"Frame {frame_count}"
                debug_info += f" | Face: {feedback['face_detected']}"
                if feedback['face_detected'] and 'confidence' in feedback:
                    debug_info += f" | Conf: {feedback['confidence']}"
                cv2.putText(processed_frame, debug_info, (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Print status
                print(f"\rFrame {frame_count} - Face: {feedback['face_detected']} | "
                      f"Status: {feedback['attention_status']}", end="")
                
                # Perform periodic analysis
                current_time = time.time()
                if current_time - last_analysis_time >= analysis_interval:
                    print("\n\nAnalyzing recent movement patterns...")
                    pose_metrics = await processor.analyze_movement(frames)
                    
                    print("\nMovement Analysis Results:")
                    print(f"- Eye contact score: {pose_metrics.eye_contact_score:.2f}%")
                    print(f"- Posture score: {pose_metrics.posture_score:.2f}%")
                    print(f"- Movement score: {pose_metrics.movement_score:.2f}")
                    print(f"- Gesture count: {pose_metrics.gesture_count}")
                    print("\nAttention Zones:")
                    for zone, percentage in pose_metrics.attention_zones.items():
                        print(f"- {zone.capitalize()}: {percentage:.1f}%")
                    
                    last_analysis_time = current_time
                
                # Display the processed frame
                cv2.imshow('Processed Frame', processed_frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n\nExiting test...")
                    break
                elif key == ord('s'):
                    filename = f'frame_{frame_count}.jpg'
                    cv2.imwrite(filename, processed_frame)
                    print(f"\nSaved frame to {filename}")
                    
                frame_count += 1
                
            except Exception as e:
                print(f"\nError processing frame {frame_count}: {str(e)}")
                continue
        
    except Exception as e:
        print(f"\nVideo processing test failed: {str(e)}")
    
    finally:
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        print("\nTest completed.")

if __name__ == "__main__":
    asyncio.run(test_video_processing())