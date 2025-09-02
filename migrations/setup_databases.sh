#!/bin/bash

# PostgreSQL Database Setup Script for Job Dashboard
# This script creates the databases and runs all migrations for the microservices

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}
DB_USER=${DB_USER:-"postgres"}
DB_PASSWORD=${DB_PASSWORD:-""}

# Database names
USER_DB="user_service_db"
RESUME_DB="resume_service_db"
AI_DB="ai_service_db"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if PostgreSQL is running
check_postgres() {
    print_status "Checking PostgreSQL connection..."
    
    if command -v psql >/dev/null 2>&1; then
        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "PostgreSQL connection successful"
            return 0
        else
            print_error "Cannot connect to PostgreSQL. Please check your connection settings."
            print_error "Host: $DB_HOST, Port: $DB_PORT, User: $DB_USER"
            return 1
        fi
    else
        print_error "psql command not found. Please install PostgreSQL client tools."
        return 1
    fi
}

# Function to create database
create_database() {
    local db_name=$1
    print_status "Creating database: $db_name"
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \"$db_name\";" >/dev/null 2>&1; then
        print_success "Database '$db_name' created successfully"
    else
        print_warning "Database '$db_name' might already exist or creation failed"
    fi
}

# Function to run migrations for a service
run_migrations() {
    local service_name=$1
    local db_name=$2
    local migration_dir=$3
    
    print_status "Running migrations for $service_name..."
    
    if [ ! -d "$migration_dir" ]; then
        print_error "Migration directory not found: $migration_dir"
        return 1
    fi
    
    # Get all SQL files in the migration directory, sorted
    migration_files=$(find "$migration_dir" -name "*.sql" | sort)
    
    if [ -z "$migration_files" ]; then
        print_warning "No migration files found in $migration_dir"
        return 0
    fi
    
    for migration_file in $migration_files; do
        print_status "Running migration: $(basename "$migration_file")"
        
        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -f "$migration_file" >/dev/null 2>&1; then
            print_success "Migration $(basename "$migration_file") completed successfully"
        else
            print_error "Migration $(basename "$migration_file") failed"
            return 1
        fi
    done
    
    print_success "All migrations for $service_name completed successfully"
}

# Function to verify database setup
verify_setup() {
    print_status "Verifying database setup..."
    
    # Check if databases exist
    for db_name in "$USER_DB" "$RESUME_DB" "$AI_DB"; do
        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "Database '$db_name' is accessible"
        else
            print_error "Database '$db_name' is not accessible"
            return 1
        fi
    done
    
    # Check if key tables exist
    print_status "Checking key tables..."
    
    # User service tables
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$USER_DB" -c "SELECT COUNT(*) FROM users;" >/dev/null 2>&1; then
        print_success "User service tables created successfully"
    else
        print_error "User service tables not found"
        return 1
    fi
    
    # Resume service tables
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$RESUME_DB" -c "SELECT COUNT(*) FROM resumes;" >/dev/null 2>&1; then
        print_success "Resume service tables created successfully"
    else
        print_error "Resume service tables not found"
        return 1
    fi
    
    # AI service tables
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$AI_DB" -c "SELECT COUNT(*) FROM ai_processing_sessions;" >/dev/null 2>&1; then
        print_success "AI service tables created successfully"
    else
        print_error "AI service tables not found"
        return 1
    fi
    
    print_success "Database setup verification completed successfully"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --host HOST       PostgreSQL host (default: localhost)"
    echo "  -p, --port PORT       PostgreSQL port (default: 5432)"
    echo "  -u, --user USER       PostgreSQL user (default: postgres)"
    echo "  -w, --password PASS   PostgreSQL password"
    echo "  --user-only           Setup only user service database"
    echo "  --resume-only         Setup only resume service database"
    echo "  --ai-only             Setup only AI service database"
    echo "  --verify-only         Only verify existing setup"
    echo "  --help                Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DB_HOST               PostgreSQL host"
    echo "  DB_PORT               PostgreSQL port"
    echo "  DB_USER               PostgreSQL user"
    echo "  DB_PASSWORD           PostgreSQL password"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Setup all databases with defaults"
    echo "  $0 -h localhost -u myuser -w mypass  # Setup with custom credentials"
    echo "  $0 --user-only                       # Setup only user service"
    echo "  $0 --verify-only                     # Verify existing setup"
}

# Parse command line arguments
SETUP_USER=true
SETUP_RESUME=true
SETUP_AI=true
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            DB_HOST="$2"
            shift 2
            ;;
        -p|--port)
            DB_PORT="$2"
            shift 2
            ;;
        -u|--user)
            DB_USER="$2"
            shift 2
            ;;
        -w|--password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        --user-only)
            SETUP_USER=true
            SETUP_RESUME=false
            SETUP_AI=false
            shift
            ;;
        --resume-only)
            SETUP_USER=false
            SETUP_RESUME=true
            SETUP_AI=false
            shift
            ;;
        --ai-only)
            SETUP_USER=false
            SETUP_RESUME=false
            SETUP_AI=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "=========================================="
    echo "  Job Dashboard Database Setup Script"
    echo "=========================================="
    echo ""
    
    # Check PostgreSQL connection
    if ! check_postgres; then
        exit 1
    fi
    
    if [ "$VERIFY_ONLY" = true ]; then
        verify_setup
        exit 0
    fi
    
    # Create databases
    if [ "$SETUP_USER" = true ]; then
        create_database "$USER_DB"
    fi
    
    if [ "$SETUP_RESUME" = true ]; then
        create_database "$RESUME_DB"
    fi
    
    if [ "$SETUP_AI" = true ]; then
        create_database "$AI_DB"
    fi
    
    # Run migrations
    if [ "$SETUP_USER" = true ]; then
        run_migrations "User Service" "$USER_DB" "user-service"
    fi
    
    if [ "$SETUP_RESUME" = true ]; then
        run_migrations "Resume Service" "$RESUME_DB" "resume-service"
    fi
    
    if [ "$SETUP_AI" = true ]; then
        run_migrations "AI Service" "$AI_DB" "ai-service"
    fi
    
    # Verify setup
    verify_setup
    
    echo ""
    echo "=========================================="
    print_success "Database setup completed successfully!"
    echo "=========================================="
    echo ""
    echo "Database Connection Details:"
    echo "  User Service:     postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$USER_DB"
    echo "  Resume Service:   postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$RESUME_DB"
    echo "  AI Service:       postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$AI_DB"
    echo ""
    echo "Next Steps:"
    echo "  1. Update your service configuration files with the database URLs"
    echo "  2. Start your microservices"
    echo "  3. Run the verification script: $0 --verify-only"
    echo ""
}

# Run main function
main "$@"

