# DocuMind - AI-Powered Document & Multimedia Question Answering

A full-stack web application that allows users to upload PDF documents, audio, and video files, then interact with an AI-powered chatbot to ask questions, get summaries, and navigate timestamps.

## Features

- **User Authentication**: Email/Password registration and Google OAuth login
- **PDF Upload & Analysis**: Upload PDF documents and extract text for Q&A
- **Audio Transcription**: Upload audio files and get AI-powered transcriptions using local Whisper
- **Video Transcription**: Upload video files with automatic transcription
- **AI-Powered Q&A**: Ask questions about uploaded content using LangChain + Groq (Llama 3.3)
- **Content Summarization**: Generate brief, detailed, or key-point summaries
- **Timestamp Extraction**: Automatic topic detection and timestamp generation for audio/video
- **Interactive Media Player**: Click timestamps to jump to specific topics in audio/video
- **User Isolation**: Each user's files and chats are private and secure

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: MongoDB Atlas
- **Authentication**: JWT tokens + Google OAuth
- **AI/ML**:
  - Groq API with Llama 3.3 70B for Q&A and summarization
  - Local Whisper (faster-whisper) for transcription
  - LangChain for document Q&A
  - HuggingFace embeddings (local, free)
  - FAISS for vector search
- **PDF Processing**: PyPDF2
- **File Storage**: Cloudinary (cloud storage for all files)
- **Testing**: Pytest with 95%+ coverage target

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Authentication**: @react-oauth/google
- **Routing**: React Router v6

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions

## Project Structure

```
DocuMind/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── auth.py      # Authentication endpoints
│   │   │           ├── files.py     # File management
│   │   │           ├── chat.py      # Q&A chat
│   │   │           ├── summarization.py
│   │   │           └── timestamps.py
│   │   ├── core/            # Core utilities
│   │   │   ├── auth.py      # JWT & password utilities
│   │   │   ├── database.py  # MongoDB connection
│   │   │   └── storage.py   # File storage
│   │   ├── models/          # Database models
│   │   │   ├── user.py      # User model
│   │   │   ├── file.py
│   │   │   ├── chat.py
│   │   │   └── ...
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic services
│   │   └── utils/           # Utility functions
│   ├── tests/               # Test suite
│   ├── storage/             # Local file storage (dev only)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── auth/        # Auth components (ProtectedRoute)
│   │   │   ├── chat/
│   │   │   ├── file/
│   │   │   └── media/
│   │   ├── contexts/        # React contexts
│   │   │   └── AuthContext.tsx
│   │   ├── pages/           # Page components
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   └── HomePage.tsx
│   │   ├── services/        # API services
│   │   │   ├── api.ts       # Axios config with JWT
│   │   │   ├── authService.ts
│   │   │   └── ...
│   │   ├── hooks/           # Custom hooks
│   │   └── types/           # TypeScript types
│   └── Dockerfile
└── docker-compose.yml       # Multi-container orchestration
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Groq API key (free at https://console.groq.com)
- Google OAuth Client ID (from Google Cloud Console)
- Cloudinary account (free at https://cloudinary.com)
- MongoDB Atlas account (free tier available)
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Environment Setup

#### 1. Backend Environment Variables

Create `backend/.env`:
```env
# Application
APP_NAME=DocuMind
ENVIRONMENT=development
DEBUG=True

# MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/documind

# Groq (Get free API key at https://console.groq.com)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.3

# Storage
STORAGE_PATH=./storage
MAX_FILE_SIZE_MB=200

# JWT Auth
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

#### 2. Frontend Environment Variables

Create `frontend/.env`:
```env
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

### Running with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DocuMind
   ```

2. **Set up environment variables** (see above)

3. **Build and start**
   ```bash
   # Set Google Client ID for frontend build
   set VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Linux/Mac
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (create .env file as shown above)

4. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install --include=dev
   ```

2. **Configure environment** (create .env file as shown above)

3. **Run development server**
   ```bash
   npm run dev
   ```

4. **Access**: http://localhost:5173

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register with email/password
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/google` - Login with Google OAuth
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user profile

### Files (Protected)
- `POST /api/v1/files/upload` - Upload a file (PDF/audio/video)
- `GET /api/v1/files/{file_id}` - Get file details
- `GET /api/v1/files/{file_id}/stream` - Stream file for media playback

### Chat (Protected)
- `POST /api/v1/chat/{file_id}/ask` - Ask a question about a file
- `GET /api/v1/chat/{file_id}/history` - Get chat history

### Summaries (Protected)
- `POST /api/v1/summaries/{file_id}/generate` - Generate summary
- `GET /api/v1/summaries/{file_id}` - Get all summaries

### Timestamps (Protected)
- `POST /api/v1/timestamps/{file_id}/extract` - Extract timestamps
- `GET /api/v1/timestamps/{file_id}` - Get timestamps

### Health Check
- `GET /` - Server status page
- `GET /health` - Application health check

## Authentication Flow

### Email/Password Registration
1. User submits email, password, and name
2. Backend creates user in MongoDB with hashed password
3. JWT access token and refresh token returned
4. Frontend stores tokens in localStorage

### Google OAuth
1. User clicks "Sign in with Google"
2. Google OAuth popup authenticates user
3. Google credential sent to backend
4. Backend verifies token with Google
5. User created/updated in database
6. JWT tokens returned

### Protected Routes
- All file, chat, summary, and timestamp endpoints require authentication
- Frontend includes JWT token in Authorization header
- 401 responses redirect to login page

## Setting Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Go to "APIs & Services" → "OAuth consent screen"
4. Configure consent screen (External, fill in app info)
5. Go to "APIs & Services" → "Credentials"
6. Create OAuth 2.0 Client ID (Web application)
7. Add Authorized JavaScript origins:
   - `http://localhost:5173` (local dev)
   - `http://localhost:3000` (Docker)
8. Copy the Client ID to your .env files

## Database Schema

### Collections

1. **users** - User accounts
   - `_id` (ObjectId) - Primary key
   - `email`, `name`, `password_hash`
   - `auth_provider` (local/google)
   - `google_id` (for OAuth users)

2. **files** - File metadata (includes `user_id`)

3. **chat_history** - Q&A conversations (includes `user_id`)

4. **summaries** - Generated summaries (includes `user_id`)

5. **timestamps** - Extracted timestamps (includes `user_id`)

## Testing

### Backend Tests
```bash
cd backend
pytest --cov=app --cov-report=html
```

### Frontend Type Check
```bash
cd frontend
npx tsc --noEmit
```

## Troubleshooting

### Common Issues

1. **"The given origin is not allowed" (Google OAuth)**
   - Add your origin to Google Cloud Console Authorized JavaScript origins
   - Wait 5 minutes for changes to propagate
   - Try incognito browser window

2. **ERR_EMPTY_RESPONSE from backend**
   - Run uvicorn with `--host 0.0.0.0`
   - Check backend terminal for error traceback

3. **bcrypt/passlib errors**
   - We use bcrypt directly (not passlib)
   - Run `pip install bcrypt>=4.0.0`

4. **MongoDB Connection Failed**
   - Ensure MongoDB Atlas whitelist includes your IP
   - Check connection string format

5. **Frontend Can't Connect to Backend**
   - Use `http://127.0.0.1:8000` instead of `localhost`
   - Check CORS settings in backend
   - Verify VITE_API_URL in frontend .env

## License

MIT License
