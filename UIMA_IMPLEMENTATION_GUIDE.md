# User Identity & Memory Architecture (UIMA) Implementation Guide

## Overview

This document describes the User Identity & Memory Architecture (UIMA) implementation for Open WebUI. UIMA enables the AI to recognize each user's profile and inject personalized context into conversations automatically.

## 🎯 Features Implemented

1. **Multi-User Authentication** - Mandatory login system ensures each user has their own session
2. **PostgreSQL Database** - Persistent data storage with visual management via Adminer
3. **User Profiles** - Customizable user profiles storing job, tone preferences, and project context
4. **Memory Bridge** - Automatic context injection into chat messages based on user profile
5. **REST API** - Complete API for profile management

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Open WebUI Frontend                       │
│              (SvelteKit - Mandatory Login)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
├──────────────────────────────────────────────────────────────┤
│  • User Authentication (auths.py)                            │
│  • User Profiles Router (user_profiles.py)                   │
│  • Memory Bridge (memory_bridge.py)                          │
│  • Chat Completion Endpoints (openai.py)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│PostgreSQL│   │  Adminer │   │  Redis   │
│  (DB)    │   │ (Visual) │   │ (Cache)  │
└──────────┘   └──────────┘   └──────────┘
```

---

## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file in the project root (copy from `.env.uima.example`):

```bash
cp .env.uima.example .env
```

The `.env` file should include:
```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://webui_user:webui_password@postgres:5432/webui_db

# Enable WebUI Authentication
WEBUI_AUTH=True

# OpenRouter API (if using)
OPENROUTER_API_KEY=your_api_key_here
```

### 2. Start Docker Services

```bash
# Start all services (PostgreSQL, Adminer, Open WebUI)
docker-compose up -d

# View logs
docker-compose logs -f open-webui

# Check service status
docker-compose ps
```

### 3. Access the Services

- **Open WebUI**: http://localhost:3000
- **Adminer** (Database Management): http://localhost:8081
- **PostgreSQL**: localhost:5432

### 4. Initial Login

1. Navigate to http://localhost:3000
2. You'll be redirected to `/auth` if not logged in
3. Sign up or login with existing credentials
4. The frontend will verify your session and load your profile

---

## 🗄️ Database Schema

### `user_profiles` Table

The migration `add_user_profiles_table.py` creates this table:

```sql
CREATE TABLE user_profiles (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL FOREIGN KEY REFERENCES user(id) ON DELETE CASCADE,
    job VARCHAR(255),
    tone_preference VARCHAR(100),
    project_context TEXT,
    preferences JSON,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL
);

CREATE INDEX ix_user_profiles_user_id ON user_profiles(user_id);
```

**Columns:**
- `id`: Unique profile identifier
- `user_id`: Foreign key to `user` table
- `job`: User's job title or profession (e.g., "Software Engineer", "Data Scientist")
- `tone_preference`: Preferred communication style (e.g., "formal", "casual", "technical")
- `project_context`: Current project details or domain knowledge to consider
- `preferences`: Additional preferences as JSON (extensible)
- `created_at`, `updated_at`: Timestamps in milliseconds

---

## 🔌 API Endpoints

All endpoints require authentication (Bearer token in Authorization header).

### Get User Profile

```http
GET /api/v1/user-profiles/profiles/user
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": "user123_1234567890",
  "user_id": "user123",
  "job": "Senior Software Engineer",
  "tone_preference": "technical",
  "project_context": "Building a distributed microservices platform using Kubernetes and gRPC",
  "preferences": {
    "language": "en",
    "response_length": "detailed"
  },
  "created_at": 1704067200000,
  "updated_at": 1704067200000
}
```

### Create/Update User Profile

```http
POST /api/v1/user-profiles/profiles/user
Authorization: Bearer <token>
Content-Type: application/json

{
  "job": "Data Scientist",
  "tone_preference": "formal",
  "project_context": "ML pipeline optimization for recommendation systems",
  "preferences": {
    "response_length": "concise",
    "include_examples": true
  }
}
```

**Response (200 OK):** Returns updated profile object

### Update Profile

```http
PUT /api/v1/user-profiles/profiles/user
Authorization: Bearer <token>
Content-Type: application/json
```

Same request/response as POST.

### Delete Profile

```http
DELETE /api/v1/user-profiles/profiles/user
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "status": true
}
```

### Get Specific User Profile (Admin)

```http
GET /api/v1/user-profiles/profiles/user/{user_id}
Authorization: Bearer <admin_token>
```

---

## 🧠 Memory Bridge System

The Memory Bridge automatically injects user context into chat messages.

### How It Works

1. **User sends a chat message**
   ```
   User: "Help me optimize this query"
   ```

2. **Memory Bridge intercepts the request**
   - Fetches user profile from PostgreSQL
   - Extracts: job, tone_preference, project_context

3. **System message is enriched**
   ```
   System: "## User Profile Context
   User: Alice Chen
   Job/Role: Senior Data Engineer
   Communication Tone: technical
   Project Context: Optimizing ETL pipelines for real-time data ingestion from Kafka
   
   Please tailor your responses considering the user's profile above."
   ```

4. **AI responds with context**
   ```
   Assistant: "As a Senior Data Engineer working with Kafka, here's an optimized approach..."
   ```

### Implementation Details

**File:** `backend/open_webui/utils/memory_bridge.py`

Key functions:
- `get_user_context()` - Fetches profile from DB
- `build_context_prompt()` - Builds system message injection
- `inject_user_context_to_messages()` - Adds context to message list
- `inject_context_to_form_data()` - Processes chat completion requests

### Integration with Chat Completion

The Memory Bridge is designed to be integrated into the OpenAI router's completion endpoint. Here's how to add it:

```python
# In backend/open_webui/routers/openai.py

from open_webui.utils.memory_bridge import MemoryBridge

# Inside the chat completion endpoint:
async def chat_completion(...):
    # ... existing code ...
    
    # Inject user context before sending to model
    form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
    
    # ... continue with completion ...
```

---

## 📊 Using Adminer for Database Management

Adminer provides a visual interface for managing the PostgreSQL database.

### Access Adminer
1. Go to http://localhost:8081
2. Select PostgreSQL as the system
3. Enter connection details:
   - **Server**: `postgres`
   - **Username**: `webui_user`
   - **Password**: `webui_password`
   - **Database**: `webui_db`

### Common Tasks

**View user_profiles table:**
1. Click "webui_db" database
2. Click "user_profiles" table
3. See all user profiles with their context

**Manually add a profile:**
```sql
INSERT INTO user_profiles (
    id, user_id, job, tone_preference, project_context, preferences, created_at, updated_at
) VALUES (
    'user123_1704067200000',
    'user123',
    'Product Manager',
    'concise',
    'Leading mobile app development team',
    '{"language": "en"}',
    1704067200000,
    1704067200000
);
```

**Update a profile:**
```sql
UPDATE user_profiles 
SET job = 'Senior Product Manager',
    updated_at = extract(epoch from now()) * 1000
WHERE user_id = 'user123';
```

---

## 🔍 Troubleshooting

### PostgreSQL Connection Failed

```
Error: Connection refused (5432)
```

**Solution:**
1. Check if PostgreSQL container is running: `docker-compose ps`
2. Wait for PostgreSQL to be healthy: `docker-compose logs postgres`
3. Verify DATABASE_URL in `.env`: Should be `postgresql://webui_user:webui_password@postgres:5432/webui_db`

### Adminer Won't Connect

```
Connection error: Unable to connect
```

**Solution:**
1. Ensure PostgreSQL is running first
2. Use server name: `postgres` (not `localhost`)
3. Try credentials: webui_user / webui_password

### User Profile Not Injected into Chat

**Verify:**
1. User is logged in (check token in localStorage)
2. Profile exists in database (check via Adminer)
3. Check backend logs for errors:
   ```bash
   docker-compose logs open-webui | grep -i "memory\|profile"
   ```

### Migration Failed

```
ERROR: Relation "user_profiles" does not exist
```

**Solution:**
1. Clear database and restart migrations:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```
2. Check alembic revision: `docker-compose exec open-webui alembic current`

---

## 🔄 Chat Flow Example

Here's a complete flow demonstrating UIMA in action:

### Setup (One-time)
```bash
# 1. Start services
docker-compose up -d

# 2. Create user account via frontend
# Sign up as: john.doe@example.com

# 3. Create profile via API
curl -X POST http://localhost:3000/api/v1/user-profiles/profiles/user \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job": "Frontend Developer",
    "tone_preference": "technical",
    "project_context": "Building React components for e-commerce platform using TypeScript and Redux"
  }'
```

### Chat Interaction
```
User Input: "How do I optimize component rendering?"

Memory Bridge Process:
1. Fetch profile from PostgreSQL
2. Build context: "Frontend Developer, React, TypeScript, Redux"
3. Inject into system message

AI Response:
"As a Frontend Developer working with React, here are optimization strategies
using React.memo and useMemo for your e-commerce platform..."
```

---

## 🛠️ Development & Maintenance

### Running Migrations

```bash
# Apply pending migrations
docker-compose exec open-webui python -m alembic upgrade head

# Check current revision
docker-compose exec open-webui python -m alembic current

# Create new migration
docker-compose exec open-webui python -m alembic revision --autogenerate -m "description"
```

### Viewing Database Logs

```bash
# PostgreSQL logs
docker-compose logs postgres

# Adminer logs (if needed)
docker-compose logs adminer
```

### Backing up the Database

```bash
# Dump database
docker-compose exec postgres pg_dump -U webui_user webui_db > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U webui_user webui_db < backup.sql
```

---

## 📈 Future Enhancements

Potential features to add to UIMA:

1. **Conversation History Analysis** - Extract insights from past chats
2. **Skill Profiling** - Auto-detect user expertise level
3. **Dynamic Context Window** - Adjust context detail based on user feedback
4. **Multi-language Support** - Store profiles in multiple languages
5. **Team Profiles** - Shared context for team environments
6. **Privacy Modes** - Encrypted sensitive profile data
7. **Analytics Dashboard** - Track profile usage and effectiveness

---

## 📝 Files Modified/Created

### New Files
- `backend/open_webui/models/user_profiles.py` - Model and CRUD operations
- `backend/open_webui/routers/user_profiles.py` - REST API endpoints
- `backend/open_webui/utils/memory_bridge.py` - Context injection logic
- `backend/open_webui/migrations/versions/add_user_profiles_table.py` - Database migration
- `.env.uima.example` - Environment configuration example

### Modified Files
- `docker-compose.yaml` - Added PostgreSQL, Adminer, Open WebUI DB config
- `backend/open_webui/main.py` - Registered user_profiles router

### Existing Infrastructure (Unchanged)
- Frontend authentication (`src/routes/+layout.svelte`)
- Database engine (`backend/open_webui/internal/db.py`)
- Chat completion endpoints (`backend/open_webui/routers/openai.py`)

---

## 🔐 Security Considerations

1. **Database Credentials** - Use strong passwords in production
2. **API Access** - Profiles are user-specific; users can only see their own
3. **Token Security** - Keep JWT tokens secure (httpOnly cookies recommended)
4. **Sensitive Data** - Don't store passwords or API keys in project_context
5. **Adminer Access** - Protect Adminer port in production (firewall/auth)

---

## 📞 Support & Documentation

- **API Documentation**: Interactive docs available at `/docs` when running backend
- **Database Adminer**: Visual management tool at http://localhost:8081
- **System Logs**: Check Docker logs with `docker-compose logs`

---

**Last Updated:** January 25, 2025
**Status:** Implementation Complete ✓
**Ready for:** Testing & Production Deployment
