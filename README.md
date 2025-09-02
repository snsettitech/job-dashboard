# Job Dashboard - AI-Powered Job Search Platform

A comprehensive job search platform with AI-powered resume optimization, job matching, and automated job scraping from major platforms.

## 🚀 Features

- **AI Resume Optimizer**: OpenAI-powered resume tailoring for specific job requirements
- **Job Scraper**: Serverless function to scrape job listings from Indeed, LinkedIn, and Glassdoor
- **Smart Job Matching**: RAFT-powered semantic matching between resumes and job postings
- **Application Tracking**: Track and manage job applications with follow-up reminders
- **Real-time Dashboard**: Live metrics and insights for your job search progress

## 🛠️ Tech Stack

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **AI Services**: OpenAI GPT-4o-mini, RAFT embeddings
- **Database**: PostgreSQL + SQLAlchemy
- **Deployment**: Netlify (Frontend) + Railway (Backend)
- **Job Scraping**: Playwright serverless functions

## 📁 Project Structure

```
job-dashboard/
├── frontend/                 # React frontend application
│   ├── netlify/             # Netlify serverless functions
│   │   └── functions/       # Job scraper function
│   ├── src/
│   │   ├── components/      # React components
│   │   └── services/        # API services
│   └── JOB_SCRAPER_README.md
├── backend/                 # FastAPI backend
├── ai-service/             # AI processing service
├── user-service/           # User management service
├── resume-service/         # Resume processing service
└── docs/                   # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for backend services)
- Git

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up job scraper (optional):**
   ```bash
   # Windows
   .\setup-scraper.ps1
   
   # Or manually:
   cd netlify/functions
   npm install
   npx playwright install chromium
   cd ../..
   ```

4. **Start development server:**
   ```bash
   npm start
   ```

5. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start backend server:**
   ```bash
   python main.py
   ```

## 📋 Available Scripts

### Frontend Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

### Job Scraper Scripts

- `.\setup-scraper.ps1` - Set up job scraper dependencies
- `node test-scraper.js` - Test scraper functionality

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

### Job Scraper Configuration

The job scraper supports configuration through the UI:
- **Keywords**: Job search terms
- **Location**: Geographic preference
- **Platforms**: Indeed, LinkedIn, Glassdoor
- **Max Results**: Number of jobs per platform

## 📚 Documentation

- [Job Scraper Documentation](./frontend/JOB_SCRAPER_README.md)
- [Development Context](./docs/DEVELOPMENT_CONTEXT.md)
- [Product Vision](./docs/PRODUCT_VISION.md)
- [Implementation Progress](./docs/IMPLEMENTATION_PROGRESS.md)

## 🚨 Important Notes

### Legal Considerations

⚠️ **Web scraping may be subject to terms of service and legal restrictions:**

1. Check each platform's Terms of Service before scraping
2. Respect rate limits to avoid being blocked
3. Only use scraped data for legitimate purposes
4. Consider providing attribution when using scraped data

### Rate Limiting

The job scraper includes built-in delays and anti-detection measures, but:
- Some platforms may block automated access
- Results may vary based on geographic location
- Website structure changes may break selectors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
