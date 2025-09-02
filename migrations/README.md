# PostgreSQL Migrations

This directory contains PostgreSQL migrations for the job dashboard microservices architecture.

## Services Covered

1. **User Service** - User authentication, profiles, and preferences
2. **Resume Service** - Resume storage, versioning, and optimization tracking
3. **AI Service** - AI processing sessions and optimization history

## Migration Structure

```
migrations/
├── README.md                           # This file
├── user-service/                       # User service migrations
│   ├── 001_initial_schema.sql         # Initial user tables
│   ├── 002_auth_tables.sql            # Authentication tables
│   └── 003_user_preferences.sql       # User preferences and profiles
├── resume-service/                     # Resume service migrations
│   ├── 001_initial_schema.sql         # Initial resume tables
│   ├── 002_version_control.sql        # Version control tables
│   ├── 003_optimization_tracking.sql  # Optimization history
│   └── 004_storage_config.sql         # Storage configuration
└── ai-service/                         # AI service migrations
    ├── 001_initial_schema.sql         # Initial AI tables
    ├── 002_processing_sessions.sql    # Processing sessions
    └── 003_optimization_history.sql   # Optimization history
```

## Database Setup

### Prerequisites

1. PostgreSQL 12+ installed
2. Database user with CREATE privileges
3. Python environment with psycopg2-binary

### Environment Variables

```bash
# User Service Database
USER_DB_URL=postgresql://user:password@localhost:5432/user_service_db

# Resume Service Database  
RESUME_DB_URL=postgresql://user:password@localhost:5432/resume_service_db

# AI Service Database
AI_DB_URL=postgresql://user:password@localhost:5432/ai_service_db
```

### Running Migrations

#### User Service
```bash
cd user-service
psql $USER_DB_URL -f ../migrations/user-service/001_initial_schema.sql
psql $USER_DB_URL -f ../migrations/user-service/002_auth_tables.sql
psql $USER_DB_URL -f ../migrations/user-service/003_user_preferences.sql
```

#### Resume Service
```bash
cd resume-service
psql $RESUME_DB_URL -f ../migrations/resume-service/001_initial_schema.sql
psql $RESUME_DB_URL -f ../migrations/resume-service/002_version_control.sql
psql $RESUME_DB_URL -f ../migrations/resume-service/003_optimization_tracking.sql
psql $RESUME_DB_URL -f ../migrations/resume-service/004_storage_config.sql
```

#### AI Service
```bash
cd ai-service
psql $AI_DB_URL -f ../migrations/ai-service/001_initial_schema.sql
psql $AI_DB_URL -f ../migrations/ai-service/002_processing_sessions.sql
psql $AI_DB_URL -f ../migrations/ai-service/003_optimization_history.sql
```

## Schema Overview

### User Service Schema

- **users** - Core user accounts with authentication
- **user_profiles** - Extended profile information
- **user_preferences** - Job search and application preferences
- **user_sessions** - Active user sessions
- **refresh_tokens** - JWT refresh tokens
- **password_resets** - Password reset tokens
- **email_verifications** - Email verification tokens

### Resume Service Schema

- **resumes** - Main resume records with metadata
- **resume_versions** - Version history for resumes
- **resume_optimizations** - Optimization attempts and results
- **resume_analyses** - Analysis results and recommendations
- **storage_configs** - Cloud storage configurations

### AI Service Schema

- **ai_processing_sessions** - AI processing session tracking
- **embeddings** - Vector embeddings storage
- **resume_optimizations** - Resume optimization results
- **job_match_analyses** - Job matching analysis results
- **optimization_history** - Historical optimization data

## Security Features

- UUID primary keys for security
- Encrypted password hashes
- JWT token management
- Session tracking with IP and user agent
- Password reset and email verification tokens
- Comprehensive audit trails

## Performance Optimizations

- Strategic indexing on frequently queried columns
- JSON fields for flexible data storage
- Partitioning considerations for large tables
- Connection pooling configuration
- Query optimization hints

## Backup and Recovery

### Creating Backups
```bash
# User Service
pg_dump $USER_DB_URL > user_service_backup.sql

# Resume Service
pg_dump $RESUME_DB_URL > resume_service_backup.sql

# AI Service
pg_dump $AI_DB_URL > ai_service_backup.sql
```

### Restoring Backups
```bash
# User Service
psql $USER_DB_URL < user_service_backup.sql

# Resume Service
psql $RESUME_DB_URL < resume_service_backup.sql

# AI Service
psql $AI_DB_URL < ai_service_backup.sql
```

## Monitoring and Maintenance

### Health Checks
```sql
-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname IN ('public')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Maintenance Tasks
```sql
-- Analyze tables for query optimization
ANALYZE;

-- Vacuum tables to reclaim space
VACUUM ANALYZE;

-- Reindex if needed
REINDEX DATABASE database_name;
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify database URL format
   - Check PostgreSQL service status
   - Confirm user permissions

2. **Migration Failures**
   - Check for existing tables
   - Verify SQL syntax
   - Review error logs

3. **Performance Issues**
   - Monitor slow queries
   - Check index usage
   - Review connection pooling

### Logs and Debugging

```bash
# Enable PostgreSQL logging
# In postgresql.conf:
log_statement = 'all'
log_min_duration_statement = 1000

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log
```

## Version Control

- All migrations are version controlled
- Each migration is idempotent
- Rollback scripts provided where applicable
- Migration order is critical - run in sequence

## Contributing

When adding new migrations:

1. Follow the naming convention: `XXX_description.sql`
2. Include both UP and DOWN migrations
3. Test migrations on development database
4. Update this README with new schema changes
5. Document any breaking changes

