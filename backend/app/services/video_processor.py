import cv2
import torch
import numpy as np
import mediapipe as mp
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel

class PoseMetrics(BaseModel):
    eye_contact_score: float = 0.0
    posture_score: float = 0.0
    movement_score: float = 0.0
    gesture_count: int = 0
    attention_zones: Dict[str, float] = {
        "center": 0.0,
        "left": 0.0,
        "right": 0.0,
        "up": 0.0,
        "down": 0.0
    }

class VideoProcessor:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        
    async def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Process a single frame for face mesh detection and tracking
        """
        try:
            if frame is None or frame.size == 0:
                raise ValueError("Invalid frame provided")

            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_height, frame_width = frame.shape[:2]
            
            # Face mesh detection
            results = self.face_mesh.process(frame_rgb)
            
            frame_metrics = {
                "face_detected": False,
                "face_position": None
            }
            
            # Process detected face mesh
            if results.multi_face_landmarks:
                frame_metrics["face_detected"] = True
                for face_landmarks in results.multi_face_landmarks:
                    # Draw the face mesh
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0,255,0), thickness=1)
                    )
                    
                    # Calculate face center using nose tip (landmark 1)
                    nose_tip = face_landmarks.landmark[1]
                    face_center_x = int(nose_tip.x * frame_width)
                    face_center_y = int(nose_tip.y * frame_height)
                    
                    # Draw face center point
                    cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 255, 0), -1)
                    
                    # Calculate face position relative to frame center
                    frame_center = (frame_width // 2, frame_height // 2)
                    frame_metrics["face_position"] = {
                        "x": face_center_x - frame_center[0],
                        "y": face_center_y - frame_center[1]
                    }
                    
                    # Calculate average landmark confidence
                    confidences = [lm.visibility or 0.0 for lm in face_landmarks.landmark]
                    frame_metrics["confidence"] = sum(confidences) / len(confidences)
                    break  # Only process the first face
            
            return frame, frame_metrics
            
        except Exception as e:
            raise Exception(f"Frame processing failed: {str(e)}")
    
    async def analyze_movement(self, frames: List[np.ndarray]) -> PoseMetrics:
        """
        Analyze movement patterns across multiple frames
        """
        try:
            if not frames:
                return PoseMetrics()

            valid_frames = [f for f in frames if f is not None and f.size > 0]
            if not valid_frames:
                return PoseMetrics()

            total_frames = len(valid_frames)
            face_detection_count = 0
            movement_scores = []
            attention_zones = {
                "center": 0,
                "left": 0,
                "right": 0,
                "up": 0,
                "down": 0
            }
            
            prev_face_pos = None
            gesture_count = 0
            
            for frame in valid_frames:
                _, metrics = await self.process_frame(frame)
                
                if metrics["face_detected"]:
                    face_detection_count += 1
                    face_pos = metrics["face_position"]
                    
                    # Calculate attention zone
                    if abs(face_pos["x"]) < 50:  # threshold for center
                        attention_zones["center"] += 1
                    elif face_pos["x"] < 0:
                        attention_zones["left"] += 1
                    else:
                        attention_zones["right"] += 1
                        
                    if face_pos["y"] < -50:
                        attention_zones["up"] += 1
                    elif face_pos["y"] > 50:
                        attention_zones["down"] += 1
                    
                    # Detect significant movements (potential gestures)
                    if prev_face_pos:
                        movement = abs(face_pos["x"] - prev_face_pos["x"]) + \
                                 abs(face_pos["y"] - prev_face_pos["y"])
                        movement_scores.append(movement)
                        if movement > 100:  # threshold for gesture detection
                            gesture_count += 1
                            
                    prev_face_pos = face_pos
            
            # Calculate final metrics
            metrics = PoseMetrics(
                eye_contact_score=face_detection_count / total_frames * 100 if total_frames > 0 else 0,
                posture_score=attention_zones["center"] / total_frames * 100 if total_frames > 0 else 0,
                movement_score=sum(movement_scores) / len(movement_scores) if movement_scores else 0,
                gesture_count=gesture_count
            )
            
            # Calculate attention zones percentages
            if total_frames > 0:
                metrics.attention_zones = {
                    zone: (count / total_frames * 100)
                    for zone, count in attention_zones.items()
                }
                
            return metrics
            
        except Exception as e:
            raise Exception(f"Movement analysis failed: {str(e)}")
            
    async def get_realtime_feedback(self, frame: np.ndarray) -> Dict:
        """
        Process frame in real-time for immediate feedback
        """
        try:
            if frame is None or frame.size == 0:
                return {
                    "face_detected": False,
                    "attention_status": "no valid frame",
                    "error": "Invalid frame provided"
                }

            _, metrics = await self.process_frame(frame)
            
            feedback = {
                "face_detected": metrics["face_detected"],
                "attention_status": "centered"
            }
            
            if metrics["face_detected"] and metrics["face_position"]:
                pos = metrics["face_position"]
                if abs(pos["x"]) > 100:
                    feedback["attention_status"] = "looking away"
                elif abs(pos["y"]) > 100:
                    feedback["attention_status"] = "poor posture"
                
                # Add confidence to feedback
                if "confidence" in metrics:
                    feedback["confidence"] = f"{metrics['confidence']:.2f}"
                    
            return feedback
            
        except Exception as e:
            return {
                "face_detected": False,
                "attention_status": "error",
                "error": str(e)
            }