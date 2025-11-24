# AI Learning Coach 🤖📚

A fully functional full-stack web application that delivers personalized AI learning experiences. The platform ingests content from multiple sources (RSS feeds, YouTube, Twitter/X, websites), processes it using RAG (Retrieval-Augmented Generation) with Gemini embeddings and Supabase pgvector, and generates personalized weekly learning digests delivered via email.

## ✨ Features

- **🎯 Personalized Learning Goals**: Set weekly learning objectives with customizable difficulty levels
- **📡 Multi-Source Content Ingestion**: Automatically collect content from RSS feeds, YouTube, Twitter/X, Reddit, and websites
- **🧠 RAG-Powered Digest Generation**: Semantic search and intelligent ranking using pgvector and Gemini AI
- **📧 Weekly Email Digests**: Automated personalized summaries delivered via MailerSend
- **🔄 Feedback Loop**: User feedback continuously improves content relevance
- **⚡ Real-time Processing**: Background jobs for content ingestion and digest generation
- **🔐 Secure Authentication**: User management with Supabase Auth

## 🚀 Quick Start

The easiest way to run the entire application:

```bash
chmod +x start.sh
./start.sh
```

This will start both the backend (port 8000) and frontend (port 3000).

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
Ai-Coach/
├── backend/              # FastAPI backend application
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configurations
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── main.py      # Application entry point
│   └── requirements.txt
├── frontend/            # Next.js frontend application
│   ├── src/
│   │   ├── app/         # Next.js App Router pages
│   │   ├── components/  # React components
│   │   └── lib/         # Utilities and helpers
│   └── package.json
├── docs/                # Documentation
│   ├── masterRAG.md    # RAG implementation guide
│   ├── database_setup.md
│   └── QUICK_START.md
├── config/             # Configuration files
│   ├── apis.md        # API specification
│   └── rss.md         # RSS feed sources
└── start.sh           # Quick start script
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database with pgvector extension
- **Gemini API** - LLM for embeddings and text generation
- **APScheduler** - Background job scheduling
- **Pydantic** - Data validation

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Hook Form** - Form management
- **Axios** - HTTP client

### External Services
- **Supabase** - Database, authentication, and vector storage
- **Google Gemini** - LLM and embeddings
- **MailerSend** - Email delivery service

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account
- Google Gemini API key
- MailerSend API key

## 🔧 Manual Setup

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.template .env
   ```
   
   Edit `.env` with your credentials:
   - `SUPABASE_URL` and `SUPABASE_KEY`
   - `GEMINI_API_KEY`
   - `MAILERSEND_API_KEY`
   - Social media API keys (optional)

5. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment:
   ```bash
   cp .env.local.template .env.local
   ```
   
   Edit `.env.local` with your backend URL

4. Run the development server:
   ```bash
   npm run dev
   ```

## 🎯 Current Status

✅ **Fully Functional**

All core features are implemented and working:
- ✅ User authentication and management
- ✅ Learning goal creation and tracking
- ✅ Multi-source content ingestion
- ✅ RAG-based content processing
- ✅ Digest generation with Gemini AI
- ✅ Email delivery with MailerSend
- ✅ Responsive Next.js frontend
- ✅ Background job scheduling

## 📖 Usage

1. **Sign Up**: Create an account at http://localhost:3000/signup
2. **Set Learning Goals**: Define what you want to learn this week
3. **Add Content Sources**: Configure RSS feeds, YouTube channels, etc.
4. **Generate Digest**: Click "Generate Digest" or wait for the scheduled job
5. **Receive Email**: Get your personalized learning digest via email
6. **Provide Feedback**: Help improve future recommendations

## 🔑 Environment Variables

### Backend (.env)
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GEMINI_API_KEY=your_gemini_api_key
MAILERSEND_API_KEY=your_mailersend_api_key
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started quickly
- **[Database Setup](docs/database_setup.md)** - Database configuration
- **[RAG Implementation](docs/masterRAG.md)** - RAG system details
- **[API Documentation](config/apis.md)** - API endpoints specification
- **[RSS Configuration](config/rss.md)** - Configure content sources

## 🧪 Testing

Test the digest generation:

```bash
# Backend must be running
curl -X POST http://localhost:8000/api/digest/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "your_user_id"}'
```

## 📄 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Built with ❤️ using FastAPI, Next.js, and Gemini AI**
