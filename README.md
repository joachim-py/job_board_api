# Job Board API

A comprehensive REST API for a job board platform built with Django REST Framework. This API supports two user types (employers and candidates) with full job posting, application management, and company profile functionality.

## 🚀 Features

### Core Functionality
- **User Management**: Registration, authentication, and profile management
- **Company Profiles**: Complete company information with logos and descriptions
- **Job Postings**: Full CRUD operations for job listings with filtering
- **Applications**: Application management with status tracking
- **Authentication**: JWT-based authentication with Djoser integration

### User Types
- **Employers**: Can create companies, post jobs, and manage applications
- **Candidates**: Can apply to jobs, upload resumes, and track application status

### Advanced Features
- **File Uploads**: Resume uploads for candidates, company logos
- **Advanced Filtering**: Search jobs by type, location, salary, company
- **Status Management**: Application workflow (Applied → Review → Interview → Offer/Reject)
- **Permissions System**: Role-based access control
- **API Documentation**: Auto-generated Swagger/ReDoc documentation

## 🛠️ Tech Stack

- **Backend**: Django 5.0+ & Django REST Framework
- **Authentication**: JWT with django-rest-framework-simplejwt
- **Database**: PostgreSQL (configurable)
- **Documentation**: drf-spectacular (OpenAPI 3.0)
- **File Storage**: Django file handling (configurable for cloud storage)
- **Filtering**: django-filter for advanced search

## 📋 Requirements

```
Django>=5.0.0
djangorestframework>=3.14.0
django-rest-framework-simplejwt>=5.3.0
djoser>=2.2.0
django-filter>=23.0
drf-spectacular>=0.27.0
Pillow>=10.0.0
python-decouple>=3.8
```

## 🚦 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <https://github.com/joachim-py/job_board_api.git>
cd job_board_api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/jobboard_db

# Security
SECRET_KEY=your-secret-key-here
DEBUG=True

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=1440  # minutes (24 hours)

# File Upload Settings
MEDIA_ROOT=media/
MEDIA_URL=/media/

# Email (for user activation)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 3. Database Setup

```bash
# Create and run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Run the Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000`

### 5. Run Tests

```bash
pytest -q
```

### 6. Continuous Integration (GitHub Actions)

A ready-made workflow is included at `.github/workflows/ci.yml`. On every push or pull request to `main`/`master` it will:

1. Check out the code.
2. Set up Python 3.12.
3. Spin up a Redis service required by Celery.
4. Install dependencies and apply migrations.
5. Execute the full test suite with `pytest -q`.

You can monitor the workflow run under the *Actions* tab of your GitHub repository.


## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/api/schema/swagger/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### Quick API Overview

#### Authentication Endpoints
```
POST   /api/token/                         # Login (get JWT tokens)
POST   /api/token/refresh/                 # Refresh JWT token
```

#### Main API Endpoints
```
# Users
GET    /api/v1/users/me/                   # Current user profile
PATCH  /api/v1/users/{id}/                 # Update profile

# Companies  
GET    /api/v1/companies/                  # List companies
POST   /api/v1/companies/                  # Create company
GET    /api/v1/companies/{id}/             # Company details

# Jobs
GET    /api/v1/jobs/                       # List jobs (with filters)
POST   /api/v1/jobs/                       # Create job (employers only)
GET    /api/v1/jobs/{id}/                  # Job details
GET    /api/v1/jobs/my_jobs/               # Employer's jobs
POST   /api/v1/jobs/{id}/toggle_active/    # Toggle job status

# Applications
GET    /api/v1/applications/               # List applications
POST   /api/v1/applications/               # Apply to job (candidates only)
GET    /api/v1/applications/my_applications/ # Candidate's applications
POST   /api/v1/applications/{id}/update_status/ # Update status (employers)

```

## 🔧 Usage Examples

### 1. User Registration

```bash
curl -X POST http://localhost:8000/api/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "employer@example.com",
    "password": "securepassword123",
    "user_type": "employer",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "employer@example.com",
    "password": "securepassword123"
  }'
```

### 3. Create a Company (Authenticated)

```bash
curl -X POST http://localhost:8000/api/v1/companies/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Tech Corp",
    "description": "Leading technology company",
    "website": "https://techcorp.com"
  }'
```

### 4. Post a Job

```bash
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Senior Python Developer",
    "job_type": "FT",
    "description": "We are looking for an experienced Python developer...",
    "location": "San Francisco, CA",
    "salary": "120000.00",
    "company": 1
  }'
```

### 5. Apply to a Job (Candidate)

```bash
curl -X POST http://localhost:8000/api/v1/applications/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer CANDIDATE_ACCESS_TOKEN" \
  -d '{
    "job": 1,
    "cover_letter": "I am very interested in this position..."
  }'
```

### 6. Filter Jobs

```bash
# Filter by job type and location
curl "http://localhost:8000/api/v1/jobs/?job_type=FT&location__icontains=francisco"

# Filter by salary range
curl "http://localhost:8000/api/v1/jobs/?salary__gte=100000&salary__lte=150000"

# Filter by company
curl "http://localhost:8000/api/v1/jobs/?company__name__icontains=tech"

```

## 🔐 Authentication & Permissions

### JWT Token Usage
```bash
# Include token in requests
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" http://localhost:8000/api/v1/jobs/
```

### Permission Levels
- **Public**: Job listings, company profiles
- **Authenticated**: User profiles, creating applications
- **Employers**: Creating jobs, managing applications for their jobs
- **Candidates**: Applying to jobs, viewing own applications
- **Owners**: Full control over own resources

## 📊 Data Models

### User Model
```python
{
  "id": 1,
  "email": "user@example.com",
  "user_type": "employer|candidate",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "company": 1  # for employers
}
```

### Job Model
```python
{
  "id": 1,
  "title": "Senior Python Developer",
  "job_type": "FT|PT|INT|CON|REM",
  "description": "Job description...",
  "location": "San Francisco, CA",
  "salary": "120000.00",
  "company": {
    "id": 1,
    "name": "Tech Corp",
    "description": "Leading technology company"
  },
  "posted_by": {
    "id": 2,
    "first_name": "Jane",
    "last_name": "Smith"
  },
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Application Model
```python
{
  "id": 1,
  "job": {...},  # Full job details
  "candidate": {...},  # Full candidate details
  "cover_letter": "I am interested...",
  "status": "APP|REV|INT|OFF|REJ",
  "applied_at": "2024-01-16T14:30:00Z"
}
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Creates htmlcov/ directory
```

## 🚀 Deployment

### Environment Variables for Production
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@db:5432/jobboard
SECRET_KEY=your-production-secret-key
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Static/Media files (use cloud storage)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "project.wsgi:application"]
```

## 📈 API Monitoring

### Health Check
```bash
curl http://localhost:8000/api/health/
# Response: {"status": "ok", "version": "v1", "message": "Job Board API is running"}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/schema/swagger/`
- Review the test files for usage examples

## 🗺️ Roadmap

- [ ] Email notifications for applications
- [ ] Real-time notifications with WebSockets
- [ ] Job recommendation system
- [ ] Analytics dashboard
- [ ] API rate limiting
- [ ] Multi-language support

Key features:
- Full-text search with fuzzy matching
- Auto-suggestions and autocomplete
- Faceted search with aggregations
- Real-time index updates
- Advanced filtering and sorting
- Search analytics