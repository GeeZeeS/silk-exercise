# Silk Exercise API

A FastAPI application for managing host asset data with MongoDB.

## Features

- Fully async implementation with FastAPI
- MongoDB integration with Motor (async MongoDB driver)
- Docker Compose setup for easy development and deployment
- Pydantic v2 for data validation and serialization
- Clean project structure with dependency injection
- Type hints and proper error handling
- Non-root user in Docker for security
- Health check endpoint for monitoring

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Running the Application

1. Clone this repository
2. Create a `.env` file with MongoDB credentials (see `.env.example`)
3. Run with Docker Compose:

```bash
docker-compose up
```

4. Access the API at http://localhost:8000
5. API documentation is available at http://localhost:8000/docs
6. Health check available at http://localhost:8000/health

## Project Structure

```
.
├── main-application/
│   ├── api/                     # API endpoints
│   │   ├── api_v1/              # API version 1
│   │   │   ├── instances/       # Instances API endpoints
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── core/                    # Core functionality
│   │   ├── instances/           # Instance-related functionality
│   │   │   ├── crud.py          # Database operations
│   │   │   ├── schemas.py       # Pydantic models for MongoDB ObjectId
│   │   │   └── __init__.py
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # MongoDB connection
│   │   └── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── Dockerfile               # Docker configuration
│   └── requirements.txt         # Python dependencies
├── .env                         # Environment variables
├── mongo-init.js                # MongoDB initialization script
├── docker-compose.yml           # Docker Compose configuration
└── README.md                    # This file
```

## API Endpoints

### Instance API (prefix: `/api/v1/instances`)

- `GET /api/v1/instances/hosts` - Get all host assets (paginated)
- `GET /api/v1/instances/hosts/{host_id}` - Get specific host asset by ID
- `GET /api/v1/instances/hosts/asset/{asset_id}` - Get host asset by asset ID
- `POST /api/v1/instances/hosts/search` - Search for host assets
- `GET /api/v1/instances/vulnerabilities/{asset_id}` - Get vulnerabilities for a host
- `GET /api/v1/instances/software/{asset_id}` - Get software for a host

### Health Check

- `GET /health` - Check API and database connection status

## Development

For local development without Docker:

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd main-application
   pip install -r requirements.txt
   ```

3. Set environment variables (see `.env` file)

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Troubleshooting

### MongoDB Connection Issues

If you encounter MongoDB connection issues (like exit code 62), try these steps:

1. Check that MongoDB container is running:
   ```bash
   docker ps
   ```

2. If the MongoDB container keeps restarting or fails, check logs:
   ```bash
   docker logs mongo_db
   ```

3. Common issues and solutions:
   - Authentication problems: Make sure the MONGODB_USER and MONGO_PASSWORD in .env match those in mongo-init.js
   - Permission issues: If using volumes, ensure proper permissions for the data directory
   - Reset MongoDB data: 
     ```bash
     docker-compose down -v
     docker-compose up
     ```

4. Check MongoDB connection with the health endpoint:
   ```
   curl http://localhost:8000/health
   ```

## Improvements Made

- Updated to Pydantic v2
- Added proper type hints throughout the codebase
- Implemented dependency injection for MongoDB connections
- Added better error handling and validation
- Optimized the Dockerfile with security best practices
- Added logging configuration
- Improved connection handling for MongoDB
- Used environment variable defaults for better configurability
- Added MongoDB initialization script
- Added health check endpoint

## License

This project is licensed under the MIT License. 