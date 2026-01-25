# UIMA Quick Setup Guide

## 5-Minute Quick Start

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

---

## Common Commands

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

---

## Verify Installation

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

---

## Troubleshooting Checklist

- [ ] Docker running? `docker ps`
- [ ] Services started? `docker-compose ps` (should show healthy)
- [ ] Can access Open WebUI? http://localhost:3000
- [ ] Can access Adminer? http://localhost:8081
- [ ] Database connection OK? Check logs: `docker-compose logs postgres`
- [ ] Auth token valid? Check localStorage after login
- [ ] Profile created? Check Adminer user_profiles table

---

## Next Steps

1. **Integrate Memory Bridge** - Modify `openai.py` to use Memory Bridge (see implementation guide)
2. **Create test suite** - Add unit tests for profile CRUD
3. **Build UI** - Add profile editor component to frontend
4. **Scale database** - Consider connection pooling for production

---

**For detailed documentation, see:** `UIMA_IMPLEMENTATION_GUIDE.md`
