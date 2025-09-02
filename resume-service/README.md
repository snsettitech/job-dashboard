# Resume Service

A microservice for resume management with S3/Railway storage integration, file processing, optimization, and analysis capabilities.

## Features

- **File Upload & Storage**: Support for PDF, DOCX, TXT, and image files with cloud storage integration
- **Text Extraction**: Advanced OCR and text extraction from various file formats
- **Resume Analysis**: AI-powered analysis of skills, experience, education, and overall quality
- **Resume Optimization**: Target-specific resume optimization with ATS scoring
- **Version Control**: Complete version history for resumes
- **Cloud Storage**: Integration with AWS S3, Railway, and local storage
- **RESTful API**: Comprehensive API with OpenAPI documentation

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │   Cloud Storage │
│                 │    │   Database      │    │   (S3/Railway)  │
│ - Resume Routes │    │ - Resume Data   │    │ - File Storage  │
│ - File Upload   │    │ - Versions      │    │ - Presigned URLs│
│ - Optimization  │    │ - Optimizations │    │                 │
│ - Analysis      │    │ - Analyses      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   File Processor │
                    │                 │
                    │ - PDF Processing │
                    │ - DOCX Processing│
                    │ - OCR (Images)  │
                    │ - Text Cleaning │
                    └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Docker & Docker Compose (optional)
- AWS S3 or Railway account (for cloud storage)

### Local Development

1. **Clone and setup**:
   ```bash
   cd resume-service
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment configuration**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Database setup**:
   ```bash
   # Start PostgreSQL (or use Docker)
   docker run -d --name postgres \
     -e POSTGRES_DB=resume_service_db \
     -e POSTGRES_USER=resume_service_user \
     -e POSTGRES_PASSWORD=resume_service_password \
     -p 5432:5432 postgres:13
   ```

4. **Run the service**:
   ```bash
   python main.py
   ```

### Docker Development

1. **Start all services**:
   ```bash
   docker-compose up -d
   ```

2. **Access services**:
   - Resume Service API: http://localhost:8002
   - API Documentation: http://localhost:8002/docs
   - pgAdmin: http://localhost:8082 (admin@resume-service.com / admin123)
   - MinIO Console: http://localhost:9002 (minioadmin / minioadmin123)

## API Endpoints

### Resume Management

- `POST /api/v1/resumes/upload` - Upload a new resume
- `GET /api/v1/resumes/` - List user resumes
- `GET /api/v1/resumes/{resume_id}` - Get specific resume
- `PUT /api/v1/resumes/{resume_id}` - Update resume
- `DELETE /api/v1/resumes/{resume_id}` - Delete resume

### Resume Versions

- `POST /api/v1/resumes/{resume_id}/versions` - Create new version
- `GET /api/v1/resumes/{resume_id}/versions` - List versions
- `GET /api/v1/resumes/{resume_id}/versions/{version_id}/download` - Download version

### Resume Optimization

- `POST /api/v1/resumes/{resume_id}/optimize` - Create optimization request
- `GET /api/v1/resumes/{resume_id}/optimizations` - List optimizations
- `GET /api/v1/optimizations/{optimization_id}` - Get optimization result

### Resume Analysis

- `POST /api/v1/resumes/{resume_id}/analyze` - Create analysis request
- `GET /api/v1/resumes/{resume_id}/analyses` - List analyses
- `GET /api/v1/analyses/{analysis_id}` - Get analysis result

### File Operations

- `GET /api/v1/resumes/{resume_id}/download` - Download resume file
- `GET /api/v1/resumes/{resume_id}/status` - Get processing status

### Health & Monitoring

- `GET /` - Service information
- `GET /health` - Health check
- `GET /health/detailed` - Detailed health check
- `GET /metrics` - Service metrics
- `GET /api/info` - API information

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment mode | `development` |
| `HOST` | Service host | `0.0.0.0` |
| `PORT` | Service port | `8002` |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `STORAGE_PROVIDER` | Storage provider (s3/railway/local) | `s3` |
| `STORAGE_BUCKET_NAME` | Storage bucket name | - |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `AWS_REGION` | AWS region | `us-east-1` |

### Storage Providers

#### AWS S3
```env
STORAGE_PROVIDER=s3
STORAGE_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

#### Railway Storage
```env
STORAGE_PROVIDER=railway
STORAGE_BUCKET_NAME=your-bucket-name
STORAGE_ENDPOINT_URL=https://your-railway-endpoint.com
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

#### Local Storage
```env
STORAGE_PROVIDER=local
LOCAL_STORAGE_PATH=./local_storage
```

## Database Schema

### Core Tables

- **resumes**: Main resume records with metadata and extracted content
- **resume_versions**: Version history for resumes
- **resume_optimizations**: Optimization attempts and results
- **resume_analyses**: Analysis results and recommendations
- **storage_configs**: Storage provider configurations

### Key Features

- UUID primary keys for security
- JSON fields for flexible data storage
- Comprehensive indexing for performance
- Foreign key relationships for data integrity

## File Processing

### Supported Formats

- **PDF**: Text extraction with OCR fallback
- **DOCX**: Full document and table extraction
- **TXT**: Plain text with encoding detection
- **Images**: OCR processing (JPG, PNG)

### Processing Pipeline

1. **File Upload**: Validation and storage
2. **Text Extraction**: Format-specific processing
3. **Content Cleaning**: Normalization and formatting
4. **Structured Analysis**: Skills, experience, education extraction
5. **Quality Assessment**: Scoring and feedback generation

## Development

### Project Structure

```
resume-service/
├── app/
│   ├── models/
│   │   ├── resume_models.py      # Database models
│   │   └── schemas.py            # Pydantic schemas
│   ├── routers/
│   │   └── resume_routes.py      # API routes
│   ├── services/
│   │   ├── resume_service.py     # Business logic
│   │   ├── storage_service.py    # Cloud storage
│   │   └── file_processor.py     # File processing
│   ├── utils/                    # Utilities
│   └── validators/               # Custom validators
├── main.py                       # FastAPI application
├── requirements.txt              # Dependencies
├── Dockerfile                    # Container configuration
├── docker-compose.yml           # Development environment
└── README.md                    # Documentation
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_resume_service.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy app/
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t resume-service .

# Run container
docker run -d \
  --name resume-service \
  -p 8002:8002 \
  -e DATABASE_URL=postgresql://... \
  -e STORAGE_PROVIDER=s3 \
  resume-service
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resume-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: resume-service
  template:
    metadata:
      labels:
        app: resume-service
    spec:
      containers:
      - name: resume-service
        image: resume-service:latest
        ports:
        - containerPort: 8002
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: resume-service-secrets
              key: database-url
```

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main branch

## Monitoring & Health Checks

### Health Endpoints

- `/health`: Basic health check
- `/health/detailed`: Detailed service status
- `/metrics`: Service metrics and statistics

### Logging

Structured logging with configurable levels:
- `INFO`: General application logs
- `ERROR`: Error conditions
- `DEBUG`: Detailed debugging information

### Metrics

- Database connection status
- Storage service health
- File processing statistics
- API request metrics

## Security

### File Upload Security

- File type validation
- File size limits (10MB default)
- Malware scanning (configurable)
- Secure file storage with access controls

### API Security

- Input validation and sanitization
- Rate limiting (configurable)
- CORS configuration
- Error handling without information leakage

### Data Protection

- Encrypted storage for sensitive data
- Secure database connections
- Audit logging for data access
- GDPR compliance features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the troubleshooting guide

## Roadmap

- [ ] Real-time processing status updates
- [ ] Advanced AI-powered resume optimization
- [ ] Integration with job boards
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile app support



