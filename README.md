# Car Companion Backend

[![CI](https://github.com/car-companion/server/actions/workflows/development_car-companion.yml/badge.svg?branch=development)](https://github.com/car-companion/server/actions/workflows/development_car-companion.yml)
![Coverage](./coverage-badge.svg)

A robust Django-based backend system for the Car Companion application, providing comprehensive vehicle management and monitoring capabilities through a RESTful API.

## Overview

The Car Companion Backend serves as the core server component of the Car Companion application, handling vehicle data management, user authentication, and real-time vehicle status monitoring. It's built using Django and Django REST Framework, following best practices for secure and scalable API development.

## Features

- **Vehicle Management**
  - Vehicle registration with VIN validation
  - Vehicle ownership management
  - Component-level status monitoring
  - Real-time vehicle state updates

- **User Management**
  - Secure user authentication using JWT
  - Role-based access control
  - Vehicle ownership and access sharing
  - Component-level permission management

- **Component Management**
  - Real-time component status monitoring
  - Component type categorization
  - Granular access control for vehicle components
  - Batch status updates for component types

- **Color and Model Management**
  - Vehicle color management with hex code validation
  - Manufacturer and model management
  - Default component configuration for vehicle models

## Technology Stack

- **Framework**: Django 5.1
- **API Framework**: Django REST Framework
- **Authentication**: JSON Web Tokens (JWT) via Djoser
- **Database**: PostgreSQL
- **Documentation**: DRF Spectacular (OpenAPI/Swagger)
- **Object-Level Permissions**: Django Guardian
- **Admin Interface**: Django Unfold
- **Containerization**: Docker & Docker Compose
- **Email Testing**: smtp4dev

## Prerequisites

- Docker and Docker Compose
- Git

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/car-companion/server.git
cd server
```

2. Create a `.env` file in the docker folder using the provided template:

```bash cd docker```
```env
# Django settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
# Database settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=usertest
DB_PASSWORD=test12345
DB_HOST=db
DB_PORT=5432
DB_SSL_MODE=disable
# Email settings
SITE_NAME=CarCompanion
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp
EMAIL_PORT=25
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@carcompanion.com
```

3. Start the services:
```bash
docker-compose up -d
```

4. Create a superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

The application will be available at:
- API: http://localhost:8000
- Email Testing Interface: http://localhost:5000
- Database: localhost:5432

### Manual Installation (Alternative)

1. Follow the same clone steps as above

2. Install Poetry:
```bash
pip install poetry
```

3. Install dependencies:
```bash
poetry install
```

4. Set up your local PostgreSQL database and configure the `.env` file accordingly

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Start the development server:
```bash
python manage.py runserver
```

## Docker Services

The application consists of three main services:

1. **Web Service**
   - Django application
   - Runs on port 8000
   - Automatically applies migrations on startup
   - Mounts static files volume

2. **Database Service**
   - PostgreSQL 13
   - Runs on port 5432
   - Persistent data storage
   - Includes health checks

3. **SMTP Service**
   - smtp4dev for email testing
   - SMTP server on port 25
   - Web interface on port 5000
   - Persistent email storage

## API Endpoints

### Authentication Endpoints
```http
# User Registration and Management
POST   /api/auth/users/                    # Register a new user
POST   /api/auth/users/activation/         # Activate user account
POST   /api/auth/users/resend_activation/  # Resend activation email
POST   /api/auth/users/reset_password/     # Request password reset
POST   /api/auth/users/reset_password_confirm/ # Confirm password reset
GET    /api/auth/users/me/                 # Get current user details
PATCH  /api/auth/users/me/                 # Update current user

# JWT Authentication
POST   /api/auth/jwt/create/              # Obtain JWT token
POST   /api/auth/jwt/refresh/             # Refresh JWT token
POST   /api/auth/jwt/verify/              # Verify JWT token
```

### Vehicle Management Endpoints
```http
# Vehicle Operations
GET    /api/car_companion/vehicles/             # List all vehicles
POST   /api/car_companion/vehicles/{vin}/take-ownership/  # Take ownership of vehicle
DELETE /api/car_companion/vehicles/{vin}/disown/         # Release vehicle ownership
GET    /api/car_companion/vehicles/accessed/    # List accessed vehicles
GET    /api/car_companion/vehicles/my-vehicles/ # List owned vehicles

# Vehicle Preferences
GET    /api/car_companion/vehicles/{vin}/preferences/  # Get vehicle preferences
PUT    /api/car_companion/vehicles/{vin}/preferences/  # Update preferences
DELETE /api/car_companion/vehicles/{vin}/preferences/  # Delete preferences
```

### Component Management Endpoints
```http
# Component Operations
GET    /api/car_companion/vehicles/{vin}/components/                    # List all components
GET    /api/car_companion/vehicles/{vin}/components/{type_name}/       # List components by type
PATCH  /api/car_companion/vehicles/{vin}/components/{type_name}/       # Update components status
GET    /api/car_companion/vehicles/{vin}/components/{type_name}/{name} # Get component details
PATCH  /api/car_companion/vehicles/{vin}/components/{type_name}/{name} # Update component status
```

### Permission Management Endpoints
```http
# Permission Overview
GET    /api/car_companion/vehicles/{vin}/permissions/overview/  # Get permissions overview

# User Permissions
GET    /api/car_companion/vehicles/{vin}/permissions/{username}/  # Get user permissions
POST   /api/car_companion/vehicles/{vin}/permissions/{username}/  # Grant permissions
DELETE /api/car_companion/vehicles/{vin}/permissions/{username}/  # Revoke permissions

# Component Type Permissions
GET    /api/car_companion/vehicles/{vin}/permissions/{username}/component/{component_type}/  # Get type permissions
POST   /api/car_companion/vehicles/{vin}/permissions/{username}/component/{component_type}/  # Grant type permissions
DELETE /api/car_companion/vehicles/{vin}/permissions/{username}/component/{component_type}/  # Revoke type permissions

# Specific Component Permissions
GET    /api/car_companion/vehicles/{vin}/permissions/{username}/component/{component_type}/{component_name}/    # Get specific permissions
POST   /api/car_companion/vehicles/{vin}/permissions/{username}/component/{component_type}/{component_name}/    # Grant specific permissions
DELETE /api/car_companion/vehicles/{vin}/permissions/{username}/component/{component_type}/{component_name}/    # Revoke specific permissions
```

### Color Management Endpoints
```http
GET    /api/car_companion/colors/    # List all colors
POST   /api/car_companion/colors/    # Create new color
```

### API Documentation
```http
GET    /api/schema/               # OpenAPI schema
GET    /api/schema/swagger-ui/    # Swagger UI documentation
GET    /api/schema/redoc/         # ReDoc documentation
```

### Health Check Endpoints
```http
GET    /health/         # System health check
```

## Authentication

The system uses JWT (JSON Web Tokens) for authentication. To authenticate:

1. Obtain a token:
```http
POST /api/auth/jwt/create/
{
    "username": "your-username",
    "password": "your-password"
}
```

2. Use the token in subsequent requests:
```http
Authorization: JWT your-token
```

## Production Deployment

For production deployment, use the production environment file with appropriate settings:

- Set `DEBUG=False`
- Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` with production domains
- Configure secure database credentials
- Set up proper email service settings
- Enable SSL/TLS for email if required

## Testing

The project includes comprehensive test coverage for models, views, and serializers. To run tests:

```bash
# Using Docker
docker-compose exec web python manage.py test

# Local environment
python manage.py test
```

For test coverage report:

```bash
# Using Docker
docker-compose exec web coverage run manage.py test
docker-compose exec web coverage report

# Local environment
coverage run manage.py test
coverage report
```

## Security Features

- JWT-based authentication
- Object-level permissions using Django Guardian
- Role-based access control
- VIN validation and standardization
- Component-level access control
- CSRF protection
- Secure password hashing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.