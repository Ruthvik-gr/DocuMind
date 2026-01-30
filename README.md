# DocuMind - AI-Powered Document & Multimedia Question Answering

A full-stack web application that allows users to upload PDF documents, audio, and video files, then interact with an AI-powered chatbot to ask questions, get summaries, and navigate timestamps.

## Features

- **PDF Upload & Analysis**: Upload PDF documents and extract text for Q&A
- **Audio Transcription**: Upload audio files and get AI-powered transcriptions using local Whisper
- **Video Transcription**: Upload video files with automatic transcription
- **AI-Powered Q&A**: Ask questions about uploaded content using LangChain + Groq (Llama 3.3)
- **Content Summarization**: Generate brief, detailed, or key-point summaries
- **Timestamp Extraction**: Automatic topic detection and timestamp generation for audio/video
- **Interactive Media Player**: Click timestamps to jump to specific topics in audio/video

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: MongoDB 7.0
- **AI/ML**:
  - Groq API with Llama 3.3 70B for Q&A and summarization
  - Local Whisper (faster-whisper) for transcription
  - LangChain for document Q&A
  - HuggingFace embeddings (local, free)
  - FAISS for vector search
- **PDF Processing**: PyPDF2
- **Testing**: Pytest with 95%+ coverage target

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **HTTP Client**: Axios

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions

## Project Structure

```
DocuMind/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Core utilities (database, storage)
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic services
│   │   └── utils/           # Utility functions
│   ├── tests/               # Test suite
│   ├── storage/             # File storage
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   ├── hooks/           # Custom hooks
│   │   └── types/           # TypeScript types
│   └── Dockerfile
└── docker-compose.yml       # Multi-container orchestration
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Groq API key (free at https://console.groq.com)
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Running with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DocuMind
   ```

2. **Set up environment variables**
   ```bash
   # Copy example env files
   cp backend/.env.example backend/.env

   # Edit backend/.env and add your Groq API key
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Start all services**
   ```bash
   docker compose up --build
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
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB**
   - Install MongoDB locally or use Docker:
     ```bash
     docker run -d -p 27017:27017 --name mongodb mongo:7.0
     ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server**
   ```bash
   npm run dev
   ```

## API Endpoints

### Files
- `POST /api/v1/files/upload` - Upload a file (PDF/audio/video)
- `GET /api/v1/files/{file_id}` - Get file details
- `GET /api/v1/files/{file_id}/stream` - Stream file for media playback

### Chat
- `POST /api/v1/chat/{file_id}/ask` - Ask a question about a file
- `GET /api/v1/chat/{file_id}/history` - Get chat history

### Summaries
- `POST /api/v1/summaries/{file_id}/generate` - Generate summary
- `GET /api/v1/summaries/{file_id}` - Get all summaries

### Timestamps
- `POST /api/v1/timestamps/{file_id}/extract` - Extract timestamps
- `GET /api/v1/timestamps/{file_id}` - Get timestamps

### Health Check
- `GET /health` - Application health check

## Testing

### Backend Tests

Run tests with coverage:
```bash
cd backend
pytest --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

### Test Structure
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for API endpoints

## Environment Variables

### Backend (.env)
```env
APP_NAME=DocuMind
ENVIRONMENT=development
DEBUG=True

MONGODB_URL=mongodb://localhost:27017/documind

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.3

STORAGE_PATH=./storage
MAX_FILE_SIZE_MB=200
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Database Schema

### Collections

1. **files** - Stores file metadata and extracted content
2. **chat_history** - Stores Q&A conversation history
3. **summaries** - Stores generated summaries
4. **timestamps** - Stores extracted timestamps for audio/video

## Features Implementation

### PDF Processing
1. Upload PDF → Validate → Store
2. Extract text using PyPDF2
3. Create vector embeddings for Q&A
4. Mark as completed

### Audio/Video Processing
1. Upload media → Validate → Store
2. Transcribe using local Whisper (faster-whisper)
3. Create vector embeddings for Q&A
4. Extract timestamps using LLM analysis
5. Mark as completed

### Q&A System
- Uses LangChain with FAISS vector store
- HuggingFace embeddings (runs locally)
- Context-aware conversations
- Source citation from relevant chunks

### Summarization
- Three types: Brief, Detailed, Key Points
- Cached in database for reuse
- Token usage tracking

### Timestamp Navigation
- LLM-based topic extraction
- Clickable timestamps in media player
- Visual highlighting of active section

## Deployment

### Using Docker Compose
```bash
docker compose up -d
```

## CI/CD

GitHub Actions workflows are configured for:
- Automated testing on pull requests
- Code coverage reporting
- Docker image building
- Linting and type checking

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running
   - Check MONGODB_URL in .env

2. **Groq API Errors**
   - Verify API key is valid
   - Check API quota

3. **File Upload Fails**
   - Check file size limits (default 200MB)
   - Verify storage directories exist and are writable

4. **Frontend Can't Connect to Backend**
   - Ensure backend is running on port 8000
   - Check CORS settings
   - Verify VITE_API_URL is correct

## License

MIT License
