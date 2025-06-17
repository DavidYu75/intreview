# Intreview - AI-Powered Interview Practice Platform

## 🚀 Overview

Intreview is an advanced AI-powered platform that helps users practice and improve their interview skills through real-time analysis of speech patterns, body language, and overall presentation. Built for FinHacks, this project combines cutting-edge AI technologies to provide comprehensive feedback on interview performance.

### 🌟 Key Features

- **Real-time Speech Analysis**: Advanced speech pattern recognition with filler word detection
- **Computer Vision Feedback**: Posture monitoring, eye contact tracking, and sentiment analysis
- **Live Performance Metrics**: Instant feedback on speaking pace, clarity, and engagement
- **Comprehensive Results**: Detailed post-interview analysis with actionable recommendations
- **Professional UI/UX**: Clean, modern interface optimized for interview practice

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **Speech Processing**: AssemblyAI integration for advanced speech analytics
- **Computer Vision**: MediaPipe for real-time facial landmark detection
- **Real-time Communication**: WebSocket connections for live feedback
- **Data Storage**: MongoDB for session and analysis data
- **Authentication**: JWT-based secure user authentication

### Frontend (React + TypeScript)
- **Modern UI**: Tailwind CSS with custom styling
- **Real-time Updates**: WebSocket integration for live feedback display
- **Interactive Components**: Dynamic progress bars and real-time metrics
- **Results Visualization**: Comprehensive analytics dashboard

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend API** | FastAPI + Python | High-performance async API |
| **Frontend** | React + TypeScript | Modern, type-safe UI |
| **Speech AI** | AssemblyAI | Advanced speech analysis |
| **Computer Vision** | MediaPipe + OpenCV | Real-time video processing |
| **Database** | MongoDB | Document storage |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **Real-time** | WebSockets | Live communication |
| **Authentication** | JWT + bcrypt | Secure user management |

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MongoDB** (local or cloud instance)
- **AssemblyAI API Key** ([Get one here](https://www.assemblyai.com/))
- **Webcam and Microphone** for interview practice

## 🎯 Core Features

### Real-time Speech Analysis
- **Words Per Minute**: Optimal speaking pace tracking (target: ~150 WPM)
- **Filler Word Detection**: Identifies "um", "like", "you know", etc.
- **Speech Intelligibility**: AI-powered clarity scoring
- **Confidence Scoring**: Word-level confidence analysis

### Computer Vision Analytics
- **Posture Monitoring**: Real-time posture assessment
- **Eye Contact Tracking**: Measures attention and engagement
- **Sentiment Analysis**: Detects positive, neutral, or negative expressions
- **Facial Landmark Detection**: 468-point facial mesh analysis

### Performance Metrics
- **Overall Performance Score**: Weighted combination of all metrics
- **Speech Analysis**: 40% intelligibility, 30% filler words, 30% pace
- **Visual Analysis**: Eye contact, posture, and sentiment scoring
- **Key Moments**: Timestamped highlights and areas for improvement

## 📊 API Endpoints

### Authentication
```
POST /auth/register    - User registration
POST /auth/token      - Login and token generation
GET  /auth/me         - Get current user info
```

### Session Management
```
POST /api/sessions/start                    - Start new interview session
POST /api/sessions/{id}/end                 - End session with analysis
GET  /api/sessions/{id}/analysis           - Get session analysis
GET  /api/sessions/history                 - Get user's session history
```

### Real-time Analysis
```
WebSocket /api/ws/video                    - Real-time video processing
POST /analysis/speech                      - Speech analysis endpoint
```

## 🔧 Development

### Project Structure
```
intreview/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # API route handlers
│   │   ├── services/            # Business logic
│   │   ├── db/models/          # Database models
│   │   └── core/               # Configuration
│   ├── main.py                 # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable components
│   │   ├── pages/             # Main page components
│   │   ├── contexts/          # React contexts
│   │   └── data/              # Static data
│   ├── public/                # Static assets
│   └── package.json
└── README.md
```

## 🎨 UI Components

### Camera Interface
- Live video feed with real-time feedback
- Recording controls and session management
- Progress indicators and metric displays
- Interview question rotation

### Results Dashboard
- Comprehensive performance analysis
- Interactive charts and progress bars
- Video playback with timestamped moments
- Downloadable PDF reports
- Actionable improvement recommendations

## 🔍 Analysis Algorithms

### Speech Intelligence Scoring
```python
speech_intelligibility = (
    weighted_confidence * 0.6 +    # Base confidence
    filler_word_score * 0.4        # Filler penalty
)
```

### Filler Word Scoring
- **Excellent**: ≤1 filler per minute (100%)
- **Good**: ≤2 fillers per minute (80%)
- **Fair**: ≤4 fillers per minute (60%)
- **Poor**: >4 fillers per minute (exponential decay)

### Visual Analysis
- **Eye Contact**: Based on face position relative to center
- **Posture**: Facial landmark positioning analysis
- **Sentiment**: Mouth curvature and facial expression detection

## 🏆 Hackathon Achievement

**Built for FinHacks 2025** - Recognized for innovation in AI-powered interview preparation technology.

## 👥 Team

- **David Yu** - Full-stack development, AI integration
- **Bew** - Frontend development, UI/UX design
