# AI Learning Coach - Backend API Specification

This document defines all backend API endpoints for the AI Learning Coach application.

## Base URL
- Development: `http://localhost:8000`
- Production: Set via `BACKEND_BASE_URL` environment variable

## Authentication
- Uses Supabase authentication
- Each request should include user context (user_id)

---

## Learning Goals API

### Create Learning Goal
**POST** `/api/goals`

Request Body:
```json
{
  "goal_text": "string",
  "difficulty_level": "beginner|intermediate|advanced",
  "frequency": "daily|weekly|biweekly"
}
```

Response:
```json
{
  "goal_id": "uuid",
  "user_id": "uuid",
  "goal_text": "string",
  "difficulty_level": "string",
  "frequency": "string",
  "is_active": true,
  "created_at": "timestamp"
}
```

### Get Active Goal
**GET** `/api/goals/active`

Response:
```json
{
  "goal_id": "uuid",
  "user_id": "uuid",
  "goal_text": "string",
  "difficulty_level": "string",
  "frequency": "string",
  "is_active": true,
  "created_at": "timestamp"
}
```

---

## Content Sources API

### Add Content Source
**POST** `/api/sources`

Request Body:
```json
{
  "source_type": "rss|youtube|reddit|x_api|website",
  "value": "string (URL, channel ID, handle, etc.)",
  "status": "active"
}
```

Response:
```json
{
  "source_id": "uuid",
  "user_id": "uuid",
  "source_type": "string",
  "value": "string",
  "status": "active",
  "created_at": "timestamp"
}
```

### List User Sources
**GET** `/api/sources`

Response:
```json
{
  "sources": [
    {
      "source_id": "uuid",
      "source_type": "string",
      "value": "string",
      "status": "active|disabled|error",
      "last_fetched_at": "timestamp|null",
      "created_at": "timestamp"
    }
  ]
}
```

---

## Digests API

### Get Current Digest
**GET** `/api/digests/current`

Response:
```json
{
  "digest_id": "uuid",
  "goal_text": "string",
  "week_start_date": "date",
  "week_end_date": "date",
  "generated_at": "timestamp",
  "total_items": "integer",
  "items": [
    {
      "digest_item_id": "uuid",
      "title": "string",
      "summary": "string",
      "why_it_matters": "string",
      "relevance_score": "float",
      "source_type": "string",
      "link_url": "string"
    }
  ]
}
```

### Get Digest History
**GET** `/api/digests/history`

Query Parameters:
- `limit`: integer (default: 10)
- `offset`: integer (default: 0)

Response:
```json
{
  "digests": [
    {
      "digest_id": "uuid",
      "goal_text": "string",
      "week_start_date": "date",
      "week_end_date": "date",
      "generated_at": "timestamp",
      "total_items": "integer"
    }
  ],
  "total_count": "integer"
}
```

### Get Specific Digest
**GET** `/api/digests/{digest_id}`

Response: Same as Current Digest format

---

## Feedback API

### Submit Feedback
**POST** `/api/feedback`

Request Body:
```json
{
  "digest_item_id": "uuid",
  "content_id": "uuid",
  "feedback_value": "useful|not_useful"
}
```

Response:
```json
{
  "feedback_id": "uuid",
  "message": "Feedback recorded successfully"
}
```

---

## Health Check

### Health Status
**GET** `/health`

Response:
```json
{
  "status": "ok",
  "timestamp": "timestamp"
}
```

---

## Error Responses

All endpoints may return standard error responses:

```json
{
  "error": "string",
  "detail": "string",
  "status_code": "integer"
}
```

Common status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error
