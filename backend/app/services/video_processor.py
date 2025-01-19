import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel

class VideoProcessor:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        
        # Key landmark indices
        # Mouth landmarks
        self.left_mouth = 61   # Left corner of mouth
        self.right_mouth = 291  # Right corner of mouth
        self.top_mouth = 13    # Top of upper lip
        self.bottom_mouth = 14  # Bottom of lower lip
        
        # Eyebrow landmarks
        self.left_inner_brow = 46   # Inner point of left eyebrow
        self.right_inner_brow = 276  # Inner point of right eyebrow
        self.left_outer_brow = 55    # Outer point of left eyebrow
        self.right_outer_brow = 285   # Outer point of right eyebrow
        self.left_mid_brow = 52      # Middle of left eyebrow
        self.right_mid_brow = 282    # Middle of right eyebrow
        
        # Points above eyebrows for reference
        self.left_forehead = 71      # Point above left eyebrow
        self.right_forehead = 301    # Point above right eyebrow
        
    def analyze_sentiment(self, landmarks) -> str:
        try:
            # Check smile first (mouth corners higher than center)
            left = landmarks.landmark[self.left_mouth]
            right = landmarks.landmark[self.right_mouth]
            top = landmarks.landmark[self.top_mouth]
            bottom = landmarks.landmark[self.bottom_mouth]
            
            mouth_corners_y = (left.y + right.y) / 2
            mouth_center_y = (top.y + bottom.y) / 2
            mouth_difference = mouth_corners_y - mouth_center_y
            
            # Determine sentiment
            if mouth_difference < -0.007:  # Smiling
                return "positive"
            else:
                return "neutral"
            
        except Exception:
            return "neutral"
        
    async def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        try:
            if frame is None or frame.size == 0:
                raise ValueError("Invalid frame provided")

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_height, frame_width = frame.shape[:2]
            
            results = self.face_mesh.process(frame_rgb)
            
            frame_metrics = {
                "face_detected": False,
                "face_position": None,
                "sentiment": "neutral"
            }
            
            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                frame_metrics["face_detected"] = True
                
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=1)
                )
                
                nose_tip = face_landmarks.landmark[1]
                face_center_x = int(nose_tip.x * frame_width)
                face_center_y = int(nose_tip.y * frame_height)
                
                cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 255, 0), -1)
                
                frame_center = (frame_width // 2, frame_height // 2)
                frame_metrics["face_position"] = {
                    "x": face_center_x - frame_center[0],
                    "y": face_center_y - frame_center[1]
                }
                
                frame_metrics["sentiment"] = self.analyze_sentiment(face_landmarks)
            
            return frame, frame_metrics
            
        except Exception as e:
            return frame, {
                "face_detected": False,
                "face_position": None,
                "sentiment": "neutral"
            }
            
    async def get_realtime_feedback(self, frame: np.ndarray) -> Dict:
        try:
            if frame is None or frame.size == 0:
                return {
                    "face_detected": False,
                    "attention_status": "no valid frame",
                    "sentiment": "neutral"
                }

            _, metrics = await self.process_frame(frame)
            
            feedback = {
                "face_detected": metrics["face_detected"],
                "attention_status": "centered",
                "sentiment": metrics["sentiment"]
            }
            
            if metrics["face_detected"] and metrics["face_position"]:
                pos = metrics["face_position"]
                if abs(pos["x"]) > frame.shape[1] * 0.2:
                    feedback["attention_status"] = "looking away"
                elif abs(pos["y"]) > frame.shape[0] * 0.2:
                    feedback["attention_status"] = "poor posture"
                    
                feedback["face_position"] = pos
                
            return feedback
                
        except Exception as e:
            return {
                "face_detected": False,
                "attention_status": "error",
                "sentiment": "neutral"
            }