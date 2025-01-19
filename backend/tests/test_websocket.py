import asyncio
import pytest
import cv2
import numpy as np
import base64
import json
import websockets
import sys
import os
from pathlib import Path
import requests
import threading
import uvicorn
import time

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

class UvicornTestServer(uvicorn.Server):
    """Uvicorn test server"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._force_exit = False
        
    def install_signal_handlers(self):
        pass

    @property
    def force_exit(self):
        return self._force_exit

    @force_exit.setter
    def force_exit(self, value):
        self._force_exit = value

    @property
    def should_exit(self):
        return self.force_exit

def run_server():
    """Run the server in a separate thread"""
    config = uvicorn.Config("main:app", host="127.0.0.1", port=8000, log_level="critical")
    server = UvicornTestServer(config=config)
    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()
    while not server.started:
        time.sleep(0.1)
    return server

async def test_websocket_connection():
    """Test basic WebSocket connection and video frame processing"""
    try:
        # First create a session using the REST API
        response = requests.post("http://localhost:8000/api/sessions/start")
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["session_id"]

        print("\nCreated test session:", session_id)

        # Connect to WebSocket
        uri = f"ws://localhost:8000/api/ws/{session_id}"
        print(f"Connecting to WebSocket at {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Create a simple test frame (black image)
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add some text to the frame
            cv2.putText(test_frame, 'Test Frame', (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', test_frame)
            base64_frame = base64.b64encode(buffer).decode('utf-8')
            
            print("Sending test frame...")
            
            # Send frame through WebSocket
            await websocket.send(json.dumps({
                "type": "video",
                "frame": base64_frame
            }))
            
            # Wait for response
            print("Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            # Verify response structure
            assert "type" in response_data
            assert response_data["type"] == "video_feedback"
            assert "feedback" in response_data
            assert "session_id" in response_data
            assert response_data["session_id"] == session_id
            
            print("\nWebSocket test successful!")
            print("Response:", json.dumps(response_data, indent=2))
            
    except Exception as e:
        pytest.fail(f"WebSocket test failed: {str(e)}")

async def test_full_interview_session():
    """Test a complete interview session with both video and audio"""
    try:
        # Start session
        response = requests.post("http://localhost:8000/api/sessions/start")
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        
        print(f"\nStarting full interview test session: {session_id}")
        
        # Connect to WebSocket
        uri = f"ws://localhost:8000/api/ws/{session_id}"
        print(f"Connecting to WebSocket at {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Simulate 5 seconds of interview
            for i in range(5):
                print(f"\nProcessing frame {i+1}/5...")
                
                # Send video frame
                test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(test_frame, f'Frame {i}', (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                _, buffer = cv2.imencode('.jpg', test_frame)
                base64_frame = base64.b64encode(buffer).decode('utf-8')
                
                await websocket.send(json.dumps({
                    "type": "video",
                    "frame": base64_frame
                }))
                
                # Get and verify video feedback
                response = await websocket.recv()
                video_feedback = json.loads(response)
                assert video_feedback["type"] == "video_feedback"
                print("Received video feedback")
                
                # Simulate audio chunk (empty bytes for test)
                await websocket.send(json.dumps({
                    "type": "audio",
                    "audio": base64.b64encode(b"").decode('utf-8')
                }))
                
                # Get and verify audio feedback
                response = await websocket.recv()
                audio_feedback = json.loads(response)
                assert audio_feedback["type"] == "audio_feedback"
                print("Received audio feedback")
                
                await asyncio.sleep(1)  # Wait 1 second between frames
                
            print("\nFull session test successful!")
                
    except Exception as e:
        pytest.fail(f"Full session test failed: {str(e)}")
    
    # End session
    try:
        response = requests.post(f"http://localhost:8000/api/sessions/{session_id}/end")
        assert response.status_code == 200
        print(f"Session {session_id} ended successfully")
    except Exception as e:
        print(f"Warning: Failed to end session: {str(e)}")

async def main():
    """Run all tests"""
    print("\nStarting WebSocket connection test...")
    await test_websocket_connection()
    
    print("\nWaiting 2 seconds before running full session test...\n")
    await asyncio.sleep(2)
    
    print("Starting full interview session test...")
    await test_full_interview_session()

if __name__ == "__main__":
    print("Starting test server...")
    server = run_server()
    print("Server started")
    
    try:
        # Run the tests
        asyncio.run(main())
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        # Clean up
        print("\nStopping server...")
        server.force_exit = True
        print("Tests completed.")