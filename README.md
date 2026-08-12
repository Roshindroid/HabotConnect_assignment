Full Name: Roshin Roy

Position: Python Backend Developer

Project name: habot_assignment

Repository: https://github.com/Roshindroid/HabotConnect_assignment.git

Mail: roshinroy050@gmail.com

## API Endpoints

### 1. Create Booking

**POST**

`/api/v1/bookings/`

Creates a new booking between a Parent and an LSA.

#### Request

```json
{
    "parent": 1,
    "lsa": 1,
    "start_time": "2026-08-15T14:00:00Z",
    "end_time": "2026-08-15T15:00:00Z"
}
```

#### Success Response

**201 Created**

```json
{
    "id": 5,
    "parent": 1,
    "lsa": 1,
    "start_time": "2026-08-15T14:00:00Z",
    "end_time": "2026-08-15T15:00:00Z",
    "status": "PENDING"
}
```

#### Possible Errors

**400 Bad Request**

Returned when:

- `end_time` is before or equal to `start_time`
- the LSA is already booked during the requested time
- the request data is invalid


### 2. Search Available LSAs

**GET**

`/api/v1/lsas/search/`

Searches active LSAs by skill and availability.

#### Query Parameters

| Parameter | Required | Description |
|---|---|---|
| `skill` | Yes | Required LSA skill |
| `start_time` | Yes | Requested session start |
| `end_time` | Yes | Requested session end |

#### Example Request

`/api/v1/lsas/search/?skill=autism&start_time=2026-08-15T12:00:00Z&end_time=2026-08-15T13:00:00Z`

#### Success Response

**200 OK**

```json
[
    {
        "id": 1,
        "name": "John",
        "email": "john@gmail.com",
        "skills": [
            "autism",
            "adhd"
        ],
        "is_active": true,
        "created_at": "2026-08-11T07:38:46.444711Z"
    }
]
```


### 3. Payment Webhook

**POST**

`/api/v1/payments/webhook/`

Receives payment status updates and updates the corresponding Payment and Booking records.

#### Successful Payment

```json
{
    "booking_id": 5,
    "transaction_id": "TXN-10001",
    "status": "SUCCESS",
    "amount": "500.00"
}
```

#### Failed Payment

```json
{
    "booking_id": 5,
    "transaction_id": "TXN-10002",
    "status": "FAILED",
    "amount": "500.00"
}
```

#### Duplicate Webhook

If the same final payment webhook is received again, the existing payment is returned instead of creating another payment.

Example response:

```json
{
    "message": "Payment webhook already processed.",
    "booking_id": 5,
    "payment_id": 5,
    "booking_status": "CONFIRMED"
}
```

## Database Design

The application uses four main entities:

- **Parent** — represents the parent requesting support.
- **LSA** — represents a Learning Support Assistant and stores their skills and availability information.
- **Booking** — represents a session requested by a Parent and assigned to an LSA.
- **Payment** — represents the payment associated with a Booking.

### Relationships

- A Parent can have multiple Bookings.
- An LSA can have multiple Bookings.
- Each Booking belongs to one Parent and one LSA.
- Each Booking can have an associated Payment.

## Query Optimization

The LSA search endpoint uses Django ORM's `Exists` and `OuterRef` to check booking availability.

A correlated subquery checks whether an LSA has any overlapping booking within the requested time range:

`OuterRef("pk")` links each LSA to its own bookings, allowing `Exists` to determine availability without loading all bookings into Python.

- `start_time < requested_end_time`
- `end_time > requested_start_time`

Cancelled and payment-failed bookings are excluded from the availability check.

Using `Exists` allows the availability check to be performed by the database instead of fetching all bookings into Python and executing a separate booking query for each LSA. This avoids the N+1 query pattern for the booking availability check.

Skill matching is currently performed in Python after the active and available LSAs have been retrieved. This keeps the implementation simple while the booking-overlap check remains database-driven.

## Architecture

This project uses Django with Django REST Framework (DRF).

Django follows the **Model-View-Template (MVT)** architectural pattern. Since this project exposes REST APIs rather than server-rendered HTML pages, the Template layer is not used for the API responses. DRF serializers handle request and response representation, while Django models manage the database layer and API views handle HTTP requests.

### Why Django MVT?

Django was chosen because it provides:

- Built-in ORM for relational database modeling.
- Django REST Framework for structured REST API development.
- Built-in validation and serialization support.
- Django's testing framework for automated tests.
- A clear separation between models, request handling, and data representation.

## Setup Instructions

## 1. Clone the repository

```bash
git clone https://github.com/Roshindroid/HabotConnect_assignment.git
cd HabotConnect_assignment
```

## 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```
## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Apply database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 5. Run the development server

```bash
python manage.py runserver
```
The API will be available at the URL: http://127.0.0.1:8000/

## 6. Run tests

```bash
python manage.py test
```

## Notes

This project is a development prototype created for the HabotConnect backend hiring assessment.

- `DEBUG=True` is intentionally enabled for local development.
- SQLite is used for local development and testing.
- The payment integration uses a mock external service implemented with `requests`.
- Production deployment settings (HTTPS, SMTP email backend, secure cookies, HSTS) have not been enabled because deployment is outside the scope of this assignment.