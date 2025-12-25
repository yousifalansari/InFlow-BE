# InFlow - Backend

## Overview
InFlow is a comprehensive invoice and quote management system designed for freelancers and small to medium-sized businesses (SMBs). This backend API powers the InFlow application, enabling users to manage clients, generate quotes, convert them to invoices, track payments, and visualize analytics.

## Features
- **User Authentication**: Secure JWT-based registration and login.
- **Client Management**: Create, read, update, and delete client profiles.
- **Quote Management**: Create quotes with line items, calculate totals, and generate PDF versions.
- **Invoice Generation**: Convert quotes to invoices, preventing duplicates, and implementing status workflows (Sent, Paid, Overdue).
- **Payment Tracking**: Record partial or full payments, automatically updating invoice balance and status.
- **Analytics**: Real-time dashboard data including monthly revenue, outstanding balances, and CSV export.
- **PDF Generation**: Professional PDF generation for Quotes and Invoices.


## Technologies Used
- **Language**: Python 3.x
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Validation**: Pydantic
- **Authentication**: PyJWT (JSON Web Tokens)
- **PDF Generation**: ReportLab
- **Testing**: Pytest, HTTPX

## Project Structure
```
InFlow-BE/
├── alembic/              # Database migration scripts
├── config/               # Configuration and environment variables
├── controllers/          # API Route Handlers (Endpoints)
├── data/                 # Data seeding scripts
├── dependencies/         # FastAPI dependencies (auth, db session)
├── models/               # SQLAlchemy Database Models
├── serializers/          # Pydantic Schemas (Request/Response)
├── database.py           # Database connection setup
├── main.py               # Application entry point
├── Pipfile               # Dependency definitions (Pipenv)
└── .env                  # Environment variables
```

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL
- Pipenv (`pip install pipenv`)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd InFlow-BE
   ```

2. **Install dependencies:**
   ```bash
   pipenv install
   ```

3. **Environment Setup:**
   Create a `.env` file in the root directory with the following variables:
   ```env
   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/inflow
   JWT_SECRET=your_super_secret_key
   ```
   *Replace values with your actual PostgreSQL credentials and a secure secret.*

4. **Initialize Database:**
   Run migrations to create tables:
   ```bash
   pipenv run alembic upgrade head
   ```

### Running the Application

Start the development server:
```bash
pipenv run uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`.

### Documentation
FastAPI automatically generates interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/register` - Register a new user
- `POST /api/login` - Login and receive JWT

### Clients
- `GET /api/clients/` - List all clients
- `POST /api/clients/` - Create a client
- `GET /api/clients/{id}` - Get client details
- `PUT /api/clients/{id}` - Update client
- `DELETE /api/clients/{id}` - Delete client

### Quotes
- `POST /api/quotes/` - Create a quote
- `GET /api/quotes/` - List quotes
- `POST /api/quotes/{id}/send` - Mark quote as sent
- `POST /api/quotes/{id}/accept` - Mark quote as accepted
- `GET /api/quotes/{id}/pdf` - Download Quote PDF

### Invoices
- `POST /api/invoices/` - Create an invoice from a quote
- `GET /api/invoices/` - List invoices
- `POST /api/invoices/{id}/send` - Mark invoice as sent
- `GET /api/invoices/{id}/pdf` - Download Invoice PDF

### Payments
- `POST /api/invoices/{id}/payments` - Record a payment
- `DELETE /api/payments/{id}` - Delete/Refund a payment

### Analytics
- `GET /api/analytics/summary` - Get financial summary
- `GET /api/analytics/export` - Export revenue data as CSV

## Database Models
- **User**: Application users (freelancers/businesses).
- **Client**: Customers of the user.
- **Quote**: Proposed work/products with line items.
- **LineItem**: Individual items within a quote.
- **Invoice**: Finalized bill derived from a quote.
- **Payment**: Transactions recorded against an invoice.

## Development Notes
- **Migrations**: When modifying models, generate a new migration:
  ```bash
  pipenv run alembic revision --autogenerate -m "description_of_change"
  pipenv run alembic upgrade head
  ```
- **Code Style**: Updates should follow the existing structure (Models -> Serializers -> Controllers).

## References & Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [GeeksforGeeks](https://www.geeksforgeeks.org/)
- [Stack Overflow](https://stackoverflow.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Frontend Repository
https://github.com/AbdullahDashti1/InFlow-FE