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

