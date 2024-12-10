[![CI](https://github.com/car-companion/server/actions/workflows/development_car-companion.yml/badge.svg?branch=development)](https://github.com/car-companion/server/actions/workflows/development_car-companion.yml)
![Coverage](./coverage-badge.svg)

# Car Companion Backend

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

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Virtual environment management tool (virtualenv, pipenv, or conda)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/car-companion/server.git
cd server
```

2. Install Poetry:
```bash
pip install poetry
```

3. Install dependencies:
```bash
poetry install
```

4. Create a `.env` file in the project root with the following variables:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

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

## API Documentation

The API documentation is available through Swagger UI and ReDoc:

- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`

## Core Models

### Vehicle
Represents a vehicle in the system with its basic information and relationships:
- VIN (Vehicle Identification Number)
- Year built
- Model (relationship to VehicleModel)
- Colors (interior and exterior)
- Owner (relationship to User)

### VehicleComponent
Represents individual components of a vehicle:
- Name
- Component type
- Status (0.0 to 1.0)
- Vehicle relationship

### ComponentPermission
Manages fine-grained access control for vehicle components:
- Component relationship
- User relationship
- Permission type (read/write)
- Valid until (optional expiration)

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

## Testing

The project includes comprehensive test coverage for models, views, and serializers. To run tests:

```bash
python manage.py test
```

For test coverage report:

```bash
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

## API Endpoints

### Vehicle Management
- `GET /api/vehicle/vehicles/`: List all vehicles
- `POST /api/vehicle/vehicles/{vin}/take-ownership/`: Take ownership of a vehicle
- `DELETE /api/vehicle/vehicles/{vin}/disown/`: Release vehicle ownership
- `PUT /api/vehicle/vehicles/{vin}/nickname/`: Update vehicle nickname

### Component Management
- `GET /api/vehicle/{vin}/components/`: List all components
- `GET /api/vehicle/{vin}/components/{type_name}/`: List components by type
- `PATCH /api/vehicle/{vin}/components/{type_name}/`: Update components status
- `GET /api/vehicle/{vin}/components/{type_name}/{name}/`: Get component details
- `PATCH /api/vehicle/{vin}/components/{type_name}/{name}/`: Update component status

### Access Management
- `GET /api/vehicle/{vin}/permissions/`: List vehicle permissions
- `POST /api/vehicle/{vin}/permissions/`: Grant vehicle access
- `GET /api/vehicle/accessed/`: List accessed vehicles

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.
