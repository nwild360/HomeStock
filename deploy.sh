#!/bin/bash
################################################################################
# HomeStock Deployment Script
#
# This script automates the deployment of HomeStock on a Debian/Ubuntu server.
# It will:
# 1. Install Docker and Docker Compose if needed
# 2. Prompt for environment configuration
# 3. Generate secure random secrets
# 4. Create .env file
# 5. Start the application with docker-compose
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Generate secure random string
generate_random_string() {
    local length=${1:-32}
    openssl rand -base64 48 | tr -d "=+/" | cut -c1-${length}
}

# Prompt with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local value

    read -p "$(echo -e ${BLUE}${prompt}${NC} [${default}]: )" value
    echo "${value:-$default}"
}

# Prompt for selection
prompt_select() {
    local prompt="$1"
    shift
    local options=("$@")

    echo -e "${BLUE}${prompt}${NC}"
    for i in "${!options[@]}"; do
        echo "  $((i+1)). ${options[$i]}"
    done

    local selection
    while true; do
        read -p "Select (1-${#options[@]}): " selection
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#options[@]}" ]; then
            echo "${options[$((selection-1))]}"
            return
        else
            print_error "Invalid selection. Please choose 1-${#options[@]}"
        fi
    done
}

# Prompt yes/no
prompt_yes_no() {
    local prompt="$1"
    local default="${2:-y}"

    local yn
    if [ "$default" = "y" ]; then
        read -p "$(echo -e ${BLUE}${prompt}${NC} [Y/n]: )" yn
        yn=${yn:-y}
    else
        read -p "$(echo -e ${BLUE}${prompt}${NC} [y/N]: )" yn
        yn=${yn:-n}
    fi

    case $yn in
        [Yy]* ) return 0;;
        * ) return 1;;
    esac
}

################################################################################
# Main Script
################################################################################

clear
print_header "HomeStock Deployment Script"

# Check if running on Debian/Ubuntu
if [ ! -f /etc/debian_version ]; then
    print_warning "This script is designed for Debian/Ubuntu systems."
    if ! prompt_yes_no "Continue anyway?"; then
        exit 1
    fi
fi

################################################################################
# Step 1: Install Dependencies
################################################################################

print_header "Step 1: Installing Dependencies"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_info "Docker not found. Installing Docker..."

    # Update package list
    sudo apt-get update

    # Install Docker
    sudo apt-get install -y docker.io

    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker

    print_success "Docker installed successfully"
else
    print_success "Docker is already installed ($(docker --version))"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_info "Docker Compose not found. Installing..."
    sudo apt-get install -y docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose is already installed ($(docker-compose --version))"
fi

# Check if user is in docker group
if ! groups $USER | grep -q docker; then
    print_info "Adding $USER to docker group..."
    sudo usermod -aG docker $USER
    print_warning "You'll need to log out and back in for docker group membership to take effect"
    print_warning "After logging back in, run this script again"
    exit 0
fi

################################################################################
# Step 2: Configure Environment
################################################################################

print_header "Step 2: Environment Configuration"

print_info "This script will help you configure your HomeStock deployment."
print_info "Press Enter to accept default values shown in brackets."
echo ""

# Environment
ENV_ENVIRONMENT=$(prompt_select "Select deployment environment:" "development" "production")

# Database Configuration
print_info "\n--- Database Configuration ---"
ENV_POSTGRES_USER=$(prompt_with_default "PostgreSQL username" "homestock_app")
ENV_POSTGRES_DB=$(prompt_with_default "PostgreSQL database name" "homestock")

# Generate or prompt for database password
if prompt_yes_no "Auto-generate secure database password?" "y"; then
    ENV_POSTGRES_PASSWORD=$(generate_random_string 32)
    print_success "Generated secure database password"
else
    read -sp "$(echo -e ${BLUE}Enter PostgreSQL password:${NC} )" ENV_POSTGRES_PASSWORD
    echo ""
    if [ -z "$ENV_POSTGRES_PASSWORD" ]; then
        print_error "Password cannot be empty"
        exit 1
    fi
fi

# CORS Configuration
print_info "\n--- CORS Configuration ---"
print_info "Enter allowed CORS origins (comma-separated URLs)"
print_info "Example: http://localhost:5173,https://yourdomain.com"

DEFAULT_CORS="http://localhost:5173"
if [ "$ENV_ENVIRONMENT" = "production" ]; then
    ENV_CORS_ORIGINS=$(prompt_with_default "CORS origins" "http://your-server-ip:5173")
else
    ENV_CORS_ORIGINS=$(prompt_with_default "CORS origins" "$DEFAULT_CORS")
fi

# JWT Configuration
print_info "\n--- JWT Configuration ---"
ENV_JWT_EXPIRY_MINUTES=$(prompt_with_default "JWT token expiry (minutes)" "30")

# Cookie Configuration
print_info "\n--- Cookie Security Configuration ---"

if [ "$ENV_ENVIRONMENT" = "production" ]; then
    print_info "Production environment detected"
    if prompt_yes_no "Are you using HTTPS?" "n"; then
        ENV_COOKIE_SECURE="true"
        ENV_COOKIE_SAMESITE="strict"
    else
        ENV_COOKIE_SECURE="false"
        ENV_COOKIE_SAMESITE="lax"
        print_warning "HTTPS is recommended for production. Cookies will be less secure."
    fi
else
    ENV_COOKIE_SECURE="false"
    ENV_COOKIE_SAMESITE="lax"
fi

# Rate Limiting
print_info "\n--- Rate Limiting Configuration ---"
ENV_RATELIMIT_ENABLED=$(prompt_with_default "Enable rate limiting" "true")

################################################################################
# Step 3: Review Configuration
################################################################################

print_header "Step 3: Review Configuration"

echo -e "${BLUE}Environment:${NC}          $ENV_ENVIRONMENT"
echo -e "${BLUE}PostgreSQL User:${NC}      $ENV_POSTGRES_USER"
echo -e "${BLUE}PostgreSQL Database:${NC}  $ENV_POSTGRES_DB"
echo -e "${BLUE}PostgreSQL Password:${NC}  ********** (hidden)"
echo -e "${BLUE}CORS Origins:${NC}         $ENV_CORS_ORIGINS"
echo -e "${BLUE}JWT Expiry:${NC}           $ENV_JWT_EXPIRY_MINUTES minutes"
echo -e "${BLUE}Cookie Secure:${NC}        $ENV_COOKIE_SECURE"
echo -e "${BLUE}Cookie SameSite:${NC}      $ENV_COOKIE_SAMESITE"
echo -e "${BLUE}Rate Limiting:${NC}        $ENV_RATELIMIT_ENABLED"

echo ""
if ! prompt_yes_no "Proceed with this configuration?" "y"; then
    print_error "Deployment cancelled by user"
    exit 1
fi

################################################################################
# Step 4: Create .env File
################################################################################

print_header "Step 4: Creating .env File"

# Backup existing .env if it exists
if [ -f .env ]; then
    BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
    print_warning "Existing .env file found. Backing up to $BACKUP_FILE"
    cp .env "$BACKUP_FILE"
fi

# Create .env file
cat > .env << EOF
# HomeStock Environment Configuration
# Generated by deploy.sh on $(date)

# Environment (development or production)
ENVIRONMENT=$ENV_ENVIRONMENT

# Database Configuration
POSTGRES_USER=$ENV_POSTGRES_USER
POSTGRES_PASSWORD=$ENV_POSTGRES_PASSWORD
POSTGRES_DB=$ENV_POSTGRES_DB

# CORS Configuration (comma-separated origins)
CORS_ORIGINS=$ENV_CORS_ORIGINS

# JWT Configuration
JWT_EXPIRY_MINUTES=$ENV_JWT_EXPIRY_MINUTES

# Cookie Security
COOKIE_SECURE=$ENV_COOKIE_SECURE
COOKIE_SAMESITE=$ENV_COOKIE_SAMESITE

# Rate Limiting
RATELIMIT_ENABLED=$ENV_RATELIMIT_ENABLED
EOF

chmod 600 .env  # Secure the .env file
print_success ".env file created successfully"

################################################################################
# Step 5: Start Services
################################################################################

print_header "Step 5: Starting Services"

print_info "Running docker-compose up -d..."
docker-compose up -d

print_success "Services started successfully"

# Wait a few seconds for services to initialize
sleep 5

################################################################################
# Step 6: Display Status and Next Steps
################################################################################

print_header "Deployment Complete!"

# Show container status
print_info "Container Status:"
docker-compose ps

echo ""
print_info "Services are running at:"
echo -e "  ${GREEN}Frontend:${NC} http://localhost:5173"
echo -e "  ${GREEN}Backend API:${NC} http://localhost:8000"
if [ "$ENV_ENVIRONMENT" = "development" ]; then
    echo -e "  ${GREEN}API Docs:${NC} http://localhost:8000/docs"
fi

echo ""
print_warning "IMPORTANT: Retrieving credentials from logs..."
sleep 3

# Extract default password from logs
DEFAULT_PASSWORD=$(docker-compose logs backend | grep "Default Password:" | tail -1 | sed -n 's/.*Default Password: \(.*\)/\1/p' | tr -d '\r')

# Display all credentials prominently
echo ""
echo -e "${RED}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                                                                          ║${NC}"
echo -e "${RED}║          SAVE THESE CREDENTIALS - THEY WILL NOT BE SHOWN AGAIN!          ║${NC}"
echo -e "${RED}║                                                                          ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  DATABASE CREDENTIALS${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Database:${NC}  $ENV_POSTGRES_DB"
echo -e "${GREEN}  Username:${NC}  $ENV_POSTGRES_USER"
echo -e "${GREEN}  Password:${NC}  $ENV_POSTGRES_PASSWORD"
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  WEB APPLICATION ADMIN CREDENTIALS${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"

if [ -n "$DEFAULT_PASSWORD" ]; then
    echo -e "${GREEN}  Username:${NC}  dev_admin"
    echo -e "${GREEN}  Password:${NC}  $DEFAULT_PASSWORD"
    echo ""
    echo -e "${RED}  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!${NC}"
else
    echo -e "${RED}  ⚠️  Could not retrieve default password from logs.${NC}"
    echo -e "${BLUE}  Run this command to view it: docker-compose logs backend | grep 'Default Password'${NC}"
fi

echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo ""
print_info "Other useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Update app:       git pull && docker-compose up -d --build"

echo ""
print_success "Deployment completed successfully!"
echo ""
