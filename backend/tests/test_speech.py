import sys
import os
import asyncio
import wave
import pyaudio
import time
from typing import Any
import scipy.io.wavfile as wavfile
import numpy as np

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.speech_analyzer import SpeechAnalyzer

async def record_audio(filename, duration=15):
    """Record audio for testing"""
    CHUNK = 1024
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    
    print("\nRecording Setup")
    print("------------------")
    print(f"Duration: {duration} seconds")
    print("\nRecording Guidelines:")
    print("- Speak naturally")
    print("- Include filler words like: um, uh, like, you know")
    print("- You can press Ctrl+C to stop early")
    
    input("\nPress Enter to start recording...")
    
    stream = p.open(format=FORMAT,
                   channels=CHANNELS,
                   rate=RATE,
                   input=True,
                   frames_per_buffer=CHUNK)
                   
    frames = []
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            print(f"\rRecording: {elapsed:.1f}s / {duration}s", end="")
            
    except KeyboardInterrupt:
        print("\n\nRecording stopped early by user")
    
    print("\nRecording complete\n")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Convert to WAV
    audio_data = np.frombuffer(b''.join(frames), dtype=np.float32)
    audio_data = np.clip(audio_data, -1.0, 1.0)
    wavfile.write(filename, RATE, (audio_data * 32767).astype(np.int16))
    
    return filename

async def test_speech_analysis():
    """Test speech analysis with recorded audio"""
    print("\nSpeech Analysis Test")
    print("=====================")
    
    try:
        analyzer = SpeechAnalyzer()
        os.makedirs("tests/data", exist_ok=True)
        audio_file = "tests/data/test_recording.wav"
        
        await record_audio(audio_file)
        
        print("Analyzing speech patterns...\n")
        metrics = await analyzer.analyze_speech(audio_file)
        
        # Print transcript
        print("Transcript")
        print("-----------")
        print(metrics.raw_transcript)
        print()
        
        # Print analysis results
        print("Analysis Results")
        print("----------------")
        print(f"Speaking Rate: {metrics.words_per_minute:.0f} words per minute")
        print(f"Speech Clarity: {metrics.clarity_score:.0%}")
        print(f"Total Filler Words: {metrics.filler_word_count}")
        
        # Group filler words by type
        single_fillers = [f for f in metrics.filler_words if f['type'] == 'single']
        multi_fillers = [f for f in metrics.filler_words if f['type'] == 'multi']
        
        if single_fillers:
            print("\nSingle-Word Fillers")
            print("-------------------")
            for filler in single_fillers:
                word_position = filler['timestamp'] + 1
                print(f"• {filler['word']} (word #{word_position})")
        
        if multi_fillers:
            print("\nMulti-Word Fillers")
            print("-----------------")
            for filler in multi_fillers:
                word_position = filler['timestamp'] + 1
                print(f"• {filler['word']} (starting at word #{word_position})")
        
        print("\nSentiment Analysis Examples")
        print("---------------------------")
        test_texts = [
            "I feel very confident about this interview opportunity",
            "I'm worried about making mistakes in the interview",
            "The interview was okay, nothing special"
        ]
        
        for test_text in test_texts:
            sentiment = await analyzer.analyze_sentiment(test_text)
            print(f"\nText: {test_text}")
            print(f"Sentiment: {sentiment['overall_sentiment']}")
            print(f"Confidence: {sentiment['confidence']:.0%}")
        
    except ValueError as e:
        print(f"\nConfiguration Error: {str(e)}")
        print("Please make sure you have set the ASSEMBLY_AI_API_KEY in your .env file")
    except Exception as e:
        print(f"\nTest Failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_speech_analysis())