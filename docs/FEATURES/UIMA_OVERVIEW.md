# UIMA (User Identity & Memory) Overview

## Overview

UIMA enables the AI to recognize each user's profile and inject personalized context into conversations automatically. This feature allows for more tailored, relevant responses based on user roles, preferences, and project context.

## Quick Start (5 Minutes)

### Prerequisites
- Docker & Docker Compose installed
- OpenRouter API key (or any LLM provider)

### Step 1: Configure Environment
```bash
cd /home/math/projets/open-webui
cp .env.uima.example .env

# Edit .env and add your OpenRouter key:
# OPENROUTER_API_KEY=sk_your_key_here
```

### Step 2: Start Services
```bash
docker-compose up -d

# Wait for PostgreSQL to be healthy (~15 seconds)
docker-compose ps
```

### Step 3: Access Services
| Service | URL | Purpose |
|---------|-----|---------|
| Open WebUI | http://localhost:3000 | Chat interface |
| Adminer | http://localhost:8081 | Database management |
| API Docs | http://localhost:3000/docs | Interactive API docs |

### Step 4: Create User & Profile

**In browser:**
1. Go to http://localhost:3000
2. Sign up with credentials (you'll be auto-redirected)
3. Copy your auth token from localStorage: `localStorage.token`

**Create profile via curl:**
```bash
TOKEN="your_token_here"

curl -X POST http://localhost:3000/api/v1/user-profiles/profiles/user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job": "Software Engineer",
    "tone_preference": "technical",
    "project_context": "Building microservices with Python and FastAPI"
  }'
```

**Or via Adminer:**
1. Go to http://localhost:8081
2. Server: postgres | User: webui_user | Password: webui_password | DB: webui_db
3. SQL command:
```sql
INSERT INTO user_profiles (id, user_id, job, tone_preference, project_context, preferences, created_at, updated_at)
VALUES ('test_1704067200000', 'user_id_here', 'Engineer', 'technical', 'Test context', '{}', 1704067200000, 1704067200000);
```

### Step 5: Test in Chat
1. Open http://localhost:3000
2. Start a conversation
3. AI should now have context about your profile!

### Common Commands

```bash
# View all services
docker-compose ps

# Check logs
docker-compose logs -f open-webui
docker-compose logs -f postgres

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Remove everything (cleanup)
docker-compose down -v
```

### Verify Installation

**Check PostgreSQL:**
```bash
docker-compose exec postgres psql -U webui_user -d webui_db -c "\dt"
# Should show: user_profiles, user, and other tables
```

**Check API:**
```bash
curl http://localhost:3000/api/v1/user-profiles/profiles/user \
  -H "Authorization: Bearer $TOKEN"
# Should return your profile (or 404 if not created)
```

**Check Adminer:**
1. Navigate to http://localhost:8081
2. Browse user_profiles table
3. See your profile data

## Architecture & Implementation

### Overview

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
└──────────────────────┬───────────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
    ▼                  ▼                  ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│PostgreSQL│   │  Adminer │   │  Redis   │
│  (DB)    │   │ (Visual) │   │ (Cache)  │
└──────────┘   └──────────┘   └──────────┘
```

### Features Implemented

1. **Multi-User Authentication** - Mandatory login system ensures each user has their own session
2. **PostgreSQL Database** - Persistent data storage with visual management via Adminer
3. **User Profiles** - Customizable user profiles storing job, tone preferences, and project context
4. **Memory Bridge** - Automatic context injection into chat messages based on user profile
5. **REST API** - Complete API for profile management

### Database Schema

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

### Memory Bridge System

The Memory Bridge automatically injects user context into chat messages.

#### How It Works

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

#### Implementation Details

**File:** `backend/open_webui/utils/memory_bridge.py`

Key functions:
- `get_user_context()` - Fetches profile from DB
- `build_context_prompt()` - Builds system message injection
- `inject_user_context_to_messages()` - Adds context to message list
- `inject_context_to_form_data()` - Processes chat completion requests

### Files Modified/Created

#### New Files
- `backend/open_webui/models/user_profiles.py` - Model and CRUD operations
- `backend/open_webui/routers/user_profiles.py` - REST API endpoints
- `backend/open_webui/utils/memory_bridge.py` - Context injection logic
- `backend/open_webui/migrations/versions/add_user_profiles_table.py` - Database migration
- `.env.uima.example` - Environment configuration example

#### Modified Files
- `docker-compose.yaml` - Added PostgreSQL, Adminer, Open WebUI DB config
- `backend/open_webui/main.py` - Registered user_profiles router

## API Reference

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

## Integration Examples

### Basic Integration in Chat Completion

At the top of `backend/open_webui/routers/openai.py`, add this import:

```python
from open_webui.utils.memory_bridge import MemoryBridge
```

In the chat completion endpoint, add this before sending to model:

```python
@router.post("/chat/completions")
async def chat_completion(request: Request, form_data: dict, user=Depends(get_verified_user)):
    # ... existing code ...
    
    # INJECT USER CONTEXT BEFORE COMPLETION
    form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
    
    # ... rest of completion logic ...
    # Send enriched form_data to model
```

### With Custom Handlers

```python
async def chat_completion(...):
    # Fetch user context
    user_context = MemoryBridge.get_user_context(user)
    
    if user_context:
        # Build custom system message
        context_prompt = MemoryBridge.build_context_prompt(user_context)
        
        # Manually inject into messages
        if form_data.get("messages"):
            form_data["messages"] = MemoryBridge.inject_user_context_to_messages(
                form_data["messages"], 
                user
            )
    
    # Continue with completion...
```

### With Logging

```python
import logging
log = logging.getLogger(__name__)

async def chat_completion(...):
    user_context = MemoryBridge.get_user_context(user)
    
    if user_context:
        log.debug(f"Injecting context for user {user.id}: {user_context}")
        form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
        log.debug(f"Modified messages: {form_data.get('messages')}")
    else:
        log.debug(f"No profile found for user {user.id}")
    
    # Continue...
```

### Step-by-Step Integration Instructions

1. **Locate the chat completion endpoint**
   File: `backend/open_webui/routers/openai.py`
   Search for: "def chat_completion" or "@router.post"
   
2. **Add import at top**
   ```python
   from open_webui.utils.memory_bridge import MemoryBridge
   ```
   
3. **Find chat completion handler**
   Look for where messages are prepared before sending to LLM model
   
4. **Add context injection**
   ```python
   # Get user from request
   user = get_verified_user(...)
   # Inject context
   if user:
       form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
   ```

5. **Test**
   - Create a user with a profile
   - Send a chat message
   - Check if system message includes profile context
   - Monitor logs for debug output

6. **Verify in Adminer**
   - Go to http://localhost:8081
   - Check user_profiles table
   - Ensure user_id matches authenticated user

### Testing the Integration

```python
import pytest
from open_webui.utils.memory_bridge import MemoryBridge
from open_webui.models.users import UserModel
from open_webui.models.user_profiles import UserProfiles

def test_memory_bridge_context_injection():
    # Create mock user
    user = UserModel(
        id="test_user_123",
        email="test@example.com",
        name="Test User",
        username="testuser",
        role="user",
        profile_image_url="",
        last_active_at=0,
        updated_at=0,
        created_at=0
    )
    
    # Create profile
    profile = UserProfiles.create_profile(
        user.id,
        UserProfileForm(
            job="Test Engineer",
            tone_preference="technical",
            project_context="Test project"
        )
    )
    
    # Test context fetch
    context = MemoryBridge.get_user_context(user)
    assert context is not None
    assert context["job"] == "Test Engineer"
    
    # Test prompt building
    prompt = MemoryBridge.build_context_prompt(context)
    assert "Test Engineer" in prompt
    assert "Test project" in prompt
    
    # Test message injection
    messages = [{"role": "user", "content": "Hello"}]
    injected = MemoryBridge.inject_user_context_to_messages(messages, user)
    
    assert len(injected) == 2  # System + user message
    assert injected[0]["role"] == "system"
    assert "Test Engineer" in injected[0]["content"]
    
    print("✅ All tests passed!")

# Run with: pytest test_memory_bridge.py
```

### API Example Flow

1. **Login to get token:**
```bash
curl -X POST http://localhost:3000/api/v1/auths/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

2. **Create user profile:**
```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

curl -X POST http://localhost:3000/api/v1/user-profiles/profiles/user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job": "Software Engineer",
    "tone_preference": "technical",
    "project_context": "Building a REST API with FastAPI"
  }'
```

3. **Send chat message (with context injection):**
```bash
curl -X POST http://localhost:3000/openai/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Help me optimize this API endpoint"}
    ]
  }'
```

## Deployment Checklist

### Backend Implementation

#### Database Layer
- [x] PostgreSQL Docker service configured
- [x] Adminer visual database tool added
- [x] Alembic migration created for `user_profiles` table
- [x] Database schema with proper foreign keys
- [x] Index on `user_id` for query optimization
- [x] Health checks configured for PostgreSQL

#### Models & Database Operations
- [x] SQLAlchemy ORM model for user_profiles
- [x] Pydantic validation models
- [x] CRUD operations (Create, Read, Update, Delete)
- [x] Database session management
- [x] Error handling for all operations
- [x] Type hints and documentation

#### REST API Endpoints
- [x] GET `/api/v1/user-profiles/profiles/user` - Get current user's profile
- [x] GET `/api/v1/user-profiles/profiles/user/{user_id}` - Get by ID (admin)
- [x] POST `/api/v1/user-profiles/profiles/user` - Create/update
- [x] PUT `/api/v1/user-profiles/profiles/user` - Update
- [x] DELETE `/api/v1/user-profiles/profiles/user` - Delete
- [x] Role-based access control (admin check)
- [x] Input validation
- [x] Error responses with proper HTTP codes

#### Memory Bridge (Context Injection)
- [x] Module for intelligent context fetching
- [x] User profile to system prompt conversion
- [x] Message list injection logic
- [x] Form data processing
- [x] Error handling with graceful fallback
- [x] Logging support for debugging

#### Framework Integration
- [x] Router imported in main.py
- [x] Router registered with FastAPI app
- [x] Proper URL prefix (/api/v1/user-profiles)
- [x] Tags for API documentation
- [x] Dependencies properly configured

### Frontend Implementation

#### Authentication
- [x] Mandatory login system (WEBUI_AUTH=True)
- [x] Token validation on every request
- [x] Redirect to /auth for unauthenticated users
- [x] Session persistence
- [x] Auto-logout on token expiry

### Configuration & Environment

#### Environment Variables
- [x] DATABASE_URL for PostgreSQL connection
- [x] WEBUI_AUTH enabled (mandatory login)
- [x] Example .env file created
- [x] Documentation for each variable

#### Docker Compose
- [x] PostgreSQL service (port 5432)
- [x] Adminer service (port 8081)
- [x] Open WebUI service (port 3000)
- [x] Service dependencies configured
- [x] Health checks for startup order
- [x] Data persistence volumes
- [x] Network connectivity between services

## Troubleshooting

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

### Memory Bridge Module Not Found

**Solution:**
- Verify file exists: `backend/open_webui/utils/memory_bridge.py`
- Restart backend: `docker-compose restart open-webui`

### Profile Not Being Injected

**Verify:**
- Check user is logged in (has valid token)
- Verify profile exists in database: `SELECT * FROM user_profiles;`
- Enable debug logging: `GLOBAL_LOG_LEVEL=DEBUG`

### System Message Not Showing in Response

**Verify:**
- Check if LLM supports system messages (most do)
- Verify message format is correct (role: "system")
- Some models filter out system messages from responses

### Performance Issues with Context Injection

**Solutions:**
- Add database query caching (Redis)
- Use connection pooling
- Consider indexing user_id (already done)

### Common Integration Issues

1. **"MemoryBridge module not found"**
   - Verify file exists: `backend/open_webui/utils/memory_bridge.py`
   - Restart backend: `docker-compose restart open-webui`

2. **"Profile not being injected"**
   - Check user is logged in (has valid token)
   - Verify profile exists in database: `SELECT * FROM user_profiles;`
   - Enable debug logging: `GLOBAL_LOG_LEVEL=DEBUG`

3. **"System message not showing in response"**
   - Check if LLM supports system messages (most do)
   - Verify message format is correct (role: "system")
   - Some models filter out system messages from responses

4. **"Performance issues with context injection"**
   - Add database query caching (Redis)
   - Use connection pooling
   - Consider indexing user_id (already done)

## Security Considerations

1. **Database Credentials** - Use strong passwords in production
2. **API Access** - Profiles are user-specific; users can only see their own
3. **Token Security** - Keep JWT tokens secure (httpOnly cookies recommended)
4. **Sensitive Data** - Don't store passwords or API keys in project_context
5. **Adminer Access** - Protect Adminer port in production (firewall/auth)

## Future Enhancements

Potential features to add to UIMA:

1. **Conversation History Analysis** - Extract insights from past chats
2. **Skill Profiling** - Auto-detect user expertise level
3. **Dynamic Context Window** - Adjust context detail based on user feedback
4. **Multi-language Support** - Store profiles in multiple languages
5. **Team Profiles** - Shared context for team environments
6. **Privacy Modes** - Encrypted sensitive profile data
7. **Analytics Dashboard** - Track profile usage and effectiveness