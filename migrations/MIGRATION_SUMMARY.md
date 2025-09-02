# PostgreSQL Migration Summary

This document provides a comprehensive overview of the PostgreSQL migrations created for the Job Dashboard microservices architecture.

## Overview

The migration system consists of **3 microservices** with **10 migration files** total, covering:

- **User Service**: Authentication, profiles, and preferences
- **Resume Service**: Resume storage, versioning, and optimization tracking
- **AI Service**: AI processing sessions and optimization history

## Migration Structure

### User Service (3 migrations)

#### 1. `001_initial_schema.sql`
- **Core Table**: `users`
- **Features**:
  - UUID primary keys for security
  - Email and username authentication
  - Profile information (title, experience, education)
  - Contact information and preferences
  - Subscription management
  - Automatic timestamp management
- **Indexes**: Email, username, creation date, active status
- **Triggers**: Automatic `updated_at` timestamp updates

#### 2. `002_auth_tables.sql`
- **Tables**: `user_sessions`, `refresh_tokens`, `password_resets`, `email_verifications`
- **Features**:
  - Session tracking with IP and user agent
  - JWT refresh token management
  - Secure password reset tokens
  - Email verification tokens
  - Automatic cleanup functions
- **Security**: Token expiration, revocation tracking, IP logging
- **Views**: Active sessions summary

#### 3. `003_user_preferences.sql`
- **Tables**: `user_profiles`, `user_preferences`
- **Features**:
  - Extended professional profiles
  - Comprehensive job search preferences
  - Skills, certifications, and languages
  - Work preferences and career goals
  - AI personalization settings
- **Functions**: Complete user profile retrieval
- **Views**: User search optimization

### Resume Service (4 migrations)

#### 1. `001_initial_schema.sql`
- **Tables**: `storage_configs`, `resumes`
- **Features**:
  - Multi-provider storage configuration (S3, Railway, Local)
  - Resume metadata and content storage
  - AI analysis results storage
  - Quality assessment tracking
  - Processing status management
- **Functions**: Storage validation and configuration retrieval
- **Default Data**: Pre-configured storage providers

#### 2. `002_version_control.sql`
- **Tables**: `resume_versions`, `resume_version_changes`
- **Features**:
  - Complete version history tracking
  - Detailed change documentation
  - Automatic version numbering
  - Change comparison functions
- **Functions**: Version creation, history retrieval, comparison
- **Triggers**: Automatic initial version creation
- **Views**: Version summary

#### 3. `003_optimization_tracking.sql`
- **Tables**: `resume_optimizations`, `resume_analyses`, `optimization_feedback`
- **Features**:
  - Optimization attempt tracking
  - Detailed analysis results
  - User feedback collection
  - Performance metrics
- **Functions**: Statistics and history retrieval
- **Views**: Performance metrics and analytics

#### 4. `004_storage_config.sql` (Integrated into 001)
- **Features**:
  - Cloud storage configuration
  - File type validation
  - Size limits and restrictions

### AI Service (3 migrations)

#### 1. `001_initial_schema.sql`
- **Tables**: `ai_processing_sessions`, `embeddings`, `ai_models`
- **Features**:
  - AI processing session tracking
  - Vector embeddings storage
  - Model performance monitoring
  - Token usage tracking
- **Functions**: Session statistics, model performance
- **Default Data**: Pre-configured AI models (GPT-4, Claude, etc.)

#### 2. `002_processing_sessions.sql`
- **Tables**: `resume_optimizations`, `job_match_analyses`, `skill_analyses`, `content_analyses`
- **Features**:
  - Resume optimization results
  - Job matching analysis
  - Skill analysis and recommendations
  - Content quality analysis
- **Functions**: Optimization and analysis statistics
- **Views**: Processing session summary and user activity

#### 3. `003_optimization_history.sql`
- **Tables**: `optimization_history`, `model_performance_history`, `user_optimization_preferences`, `optimization_templates`
- **Features**:
  - Historical optimization tracking
  - Model performance over time
  - User preference learning
  - Reusable optimization templates
- **Functions**: History statistics, performance trends, user insights
- **Views**: Analytics and performance metrics
- **Default Data**: Pre-configured optimization templates

## Key Features

### Security
- **UUID Primary Keys**: All tables use UUIDs for security
- **Encrypted Passwords**: Password hashes stored securely
- **Token Management**: Secure JWT and session token handling
- **IP Logging**: Session and token IP tracking
- **Expiration**: Automatic token and session expiration

### Performance
- **Strategic Indexing**: Optimized indexes on frequently queried columns
- **JSONB Fields**: Flexible data storage with JSONB for complex data
- **Connection Pooling**: Database connection optimization
- **Query Optimization**: Functions and views for common queries

### Scalability
- **Microservice Architecture**: Separate databases per service
- **Version Control**: Complete audit trails for changes
- **Historical Data**: Comprehensive history tracking
- **Analytics**: Built-in performance and usage analytics

### Flexibility
- **JSONB Storage**: Flexible schema for evolving requirements
- **Template System**: Reusable optimization patterns
- **Multi-Provider Support**: Storage and AI provider abstraction
- **Extensible Design**: Easy to add new features and tables

## Database Statistics

### Tables Created
- **User Service**: 7 tables
- **Resume Service**: 8 tables  
- **AI Service**: 10 tables
- **Total**: 25 tables

### Functions Created
- **User Service**: 3 functions
- **Resume Service**: 6 functions
- **AI Service**: 8 functions
- **Total**: 17 functions

### Views Created
- **User Service**: 2 views
- **Resume Service**: 4 views
- **AI Service**: 5 views
- **Total**: 11 views

### Indexes Created
- **User Service**: 20+ indexes
- **Resume Service**: 25+ indexes
- **AI Service**: 30+ indexes
- **Total**: 75+ indexes

## Setup Instructions

### Prerequisites
1. PostgreSQL 12+ installed
2. Database user with CREATE privileges
3. psql client tools installed

### Quick Setup
```bash
# Linux/Mac
chmod +x migrations/setup_databases.sh
./migrations/setup_databases.sh

# Windows
migrations\setup_databases.bat
```

### Manual Setup
```bash
# Create databases
createdb user_service_db
createdb resume_service_db
createdb ai_service_db

# Run migrations (in order)
psql -d user_service_db -f migrations/user-service/001_initial_schema.sql
psql -d user_service_db -f migrations/user-service/002_auth_tables.sql
psql -d user_service_db -f migrations/user-service/003_user_preferences.sql

psql -d resume_service_db -f migrations/resume-service/001_initial_schema.sql
psql -d resume_service_db -f migrations/resume-service/002_version_control.sql
psql -d resume_service_db -f migrations/resume-service/003_optimization_tracking.sql

psql -d ai_service_db -f migrations/ai-service/001_initial_schema.sql
psql -d ai_service_db -f migrations/ai-service/002_processing_sessions.sql
psql -d ai_service_db -f migrations/ai-service/003_optimization_history.sql
```

## Environment Configuration

### Database URLs
```bash
# User Service
DATABASE_URL=postgresql://user:password@localhost:5432/user_service_db

# Resume Service
DATABASE_URL=postgresql://user:password@localhost:5432/resume_service_db

# AI Service
DATABASE_URL=postgresql://user:password@localhost:5432/ai_service_db
```

### Required Extensions
- `uuid-ossp`: For UUID generation
- `pgvector`: For vector embeddings (optional, for AI service)

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

-- Clean up expired data (user service)
SELECT cleanup_expired_auth_data();
```

## Backup and Recovery

### Creating Backups
```bash
# User Service
pg_dump user_service_db > user_service_backup.sql

# Resume Service
pg_dump resume_service_db > resume_service_backup.sql

# AI Service
pg_dump ai_service_db > ai_service_backup.sql
```

### Restoring Backups
```bash
# User Service
psql user_service_db < user_service_backup.sql

# Resume Service
psql resume_service_db < resume_service_backup.sql

# AI Service
psql ai_service_db < ai_service_backup.sql
```

## Troubleshooting

### Common Issues
1. **Connection Errors**: Verify PostgreSQL service and credentials
2. **Migration Failures**: Check for existing tables and SQL syntax
3. **Performance Issues**: Monitor slow queries and index usage
4. **Permission Errors**: Ensure database user has CREATE privileges

### Logs and Debugging
```bash
# Enable PostgreSQL logging
# In postgresql.conf:
log_statement = 'all'
log_min_duration_statement = 1000

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log
```

## Future Enhancements

### Planned Features
- **Partitioning**: For large tables (optimization_history, processing_sessions)
- **Replication**: For high availability
- **Sharding**: For horizontal scaling
- **Advanced Analytics**: More sophisticated reporting views
- **Real-time Monitoring**: Live performance dashboards

### Migration Strategy
- **Version Control**: All migrations are version controlled
- **Rollback Support**: DOWN migrations for safe rollbacks
- **Testing**: Comprehensive testing before production deployment
- **Documentation**: Detailed documentation for each migration

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the migration logs
3. Verify database connectivity
4. Test migrations in development first

The migration system is designed to be robust, scalable, and maintainable for the Job Dashboard microservices architecture.

