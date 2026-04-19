# Specification: Orchestrateur Pédagogique Déterministe (Learning Orchestrator)

**Version:** 1.1  
**Date:** 2026-04-19  
**Status:** Architecture Analysis & Specification

---

## 1. Executive Summary

This document details the integration of a deterministic learning pathway system into Open-WebUI. The system will guide users through 6 structured learning steps via a dedicated interface component, using FastAPI as a middleware orchestrator and PostgreSQL for state management.

**Key Decision:** Implementation **uses OpenWebUI's native Function + Action system** rather than a separate button/middleware. This is better integrated and avoids polluting the standard chat flow.

---

## 2. Current Stack Analysis

### Frontend (Svelte + SvelteKit)
- **Framework:** SvelteKit 2.5.27 + Svelte 5.0.0
- **Build:** Vite 5.4.21
- **Styling:** Tailwind CSS 4.0.0
- **HTTP:** Native fetch API
- **State Management:** Svelte stores
- **UI Components:** Custom Svelte components

**Key Finding:** OpenWebUI already has a **Function/Action system**:
- Functions are stored in DB (table: `function`)
- Frontend calls `POST /api/chat/actions/{action_id}` with form data
- Backend loads function module and executes `action()` function
- Response is streamed back to chat UI

### Backend (FastAPI + Python)
- **Framework:** FastAPI
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **Models:** User, Chat, Message, Function, Prompt, etc.
- **LLM Integration:** OpenAI-compatible API (OpenRouter via `OPENAI_API_BASE_URL`)
- **Existing Routers:** `/api/chat/actions/{action_id}`, `/api/chat/completions`, etc.

**Key Finding:** OpenWebUI already integrates with OpenRouter:
- Docker compose sets `OPENAI_API_BASE_URL=https://openrouter.ai/api/v1`
- Standard OpenAI client library is used

### Database (PostgreSQL)
- **ORM:** SQLAlchemy
- **Tables:** `user`, `chat`, `message`, `function`, `prompt`, `user_profile`, etc.
- **Pattern:** All models in `backend/open_webui/models/`

---

## 3. Is the "Action Button" the Best Choice?

### Analysis: Native Function/Action vs Custom Middleware

| Criteria | Native Function/Action | Custom FastAPI Middleware |
|----------|----------------------|--------------------------|
| **Integration** | ✅ Seamless | ⚠️ External endpoint |
| **UI Discovery** | ✅ Auto-registered in OpenWebUI | ❌ Manual button management |
| **State Access** | ✅ Full request context, user object | ⚠️ Need to lookup separately |
| **Error Handling** | ✅ Built-in error propagation | ⚠️ Custom error handling |
| **Monitoring** | ✅ Integrated with function logs | ⚠️ Separate logging system |
| **Scalability** | ✅ Uses existing infrastructure | ⚠️ Additional service to manage |
| **User Experience** | ✅ Appears as action in message context menu | ✅ Dedicated button (visible always) |

### **Recommendation: Use Native Function/Action System**

**Why:** OpenWebUI's native Function system provides:
1. **Auto-discovery** in the UI
2. **User context** automatically passed
3. **Existing infrastructure** for database storage
4. **Error handling** already implemented
5. **No additional services** to manage

### Alternative Approach (Hybrid)
If a persistent button is critical (not action-on-message), we can:
1. Use the Function/Action system for the backend logic
2. Create a custom UI component in the chat interface to trigger it
3. Store trigger preference in `user_profiles` table

---

## 4. Functional Architecture

### 4.1 Database Schema

#### New Table: `user_learning_progress`
```sql
CREATE TABLE user_learning_progress (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) FOREIGN KEY REFERENCES "user"(id),
    current_step INTEGER DEFAULT 1 CHECK (current_step >= 1 AND current_step <= 6),
    step_data JSONB DEFAULT '{}',  -- Store step-specific state
    last_step_at BIGINT,            -- Timestamp of last step completion
    completed_at BIGINT,            -- When user completed all steps
    created_at BIGINT,
    updated_at BIGINT,
    UNIQUE(user_id)
);

-- Index for fast lookups
CREATE INDEX idx_user_learning_progress_user_id ON user_learning_progress(user_id);
```

#### Prompt Storage: `learning_prompts` (optional, can use files)
If we want to store prompts in DB instead of files:
```sql
CREATE TABLE learning_prompts (
    step_id INTEGER PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    instructions TEXT,     -- Pedagogical directives for the LLM
    created_at BIGINT,
    updated_at BIGINT
);
```

**Decision:** Start with **file-based prompts** (simpler, no migrations), migrate to DB if needed.

### 4.2 Prompt File Structure

**Directory:** `/backend/open_webui/learning/prompts/`

```
prompts/
├── step_1.txt   # Overview/panorama
├── step_2.txt   # Deep dive concept 1
├── step_3.txt   # Deep dive concept 2
├── step_4.txt   # Practice/application
├── step_5.txt   # Self-assessment quiz
├── step_6.txt   # Final synthesis/bonus
└── config.json  # Metadata (optional)
```

**Example Step 1 Content:**
```
You are a pedagogical tutor assisting a user in their learning journey.
Current step: 1/6 - Overview

GUIDELINES:
- Provide a panoramic view of the topic
- Use analogies and concrete examples
- Keep response concise (200-300 words)
- Ask 1-2 check-in questions to gauge understanding
- Do NOT jump to implementation details

USER CONTEXT:
[Injected from database]

USER MESSAGE:
{user_message}

RESPONSE:
```

### 4.3 Backend Components

#### A) Python Model: `UserLearningProgress`
**File:** `backend/open_webui/models/learning.py`

```python
from sqlalchemy import Column, Integer, String, JSON, BigInteger
from open_webui.internal.db import Base
from pydantic import BaseModel
from typing import Optional

class UserLearningProgress(Base):
    __tablename__ = "user_learning_progress"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    current_step = Column(Integer, default=1)
    step_data = Column(JSON, nullable=True)
    last_step_at = Column(BigInteger, nullable=True)
    completed_at = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)

class UserLearningProgressModel(BaseModel):
    id: int
    user_id: str
    current_step: int
    step_data: Optional[dict] = None
    last_step_at: Optional[int] = None
    completed_at: Optional[int] = None
```

#### B) Function Module: Learning Tutor Action
**File:** `backend/open_webui/functions/learning_tutor.py`

This module will:
1. ✅ Check/create user in `user_learning_progress`
2. ✅ Load the current step prompt from file
3. ✅ Inject user context and message
4. ✅ Call OpenRouter via standard OpenAI client
5. ✅ Return response to OpenWebUI

**Function Metadata (stored in DB):**
```json
{
    "id": "learning_tutor",
    "name": "Learning Tutor",
    "description": "Guided learning pathway with structured steps",
    "tags": ["learning", "tutor", "structured"],
    "action": true,
    "meta": {
        "usage": "Click to get help on your current learning step"
    }
}
```

### 4.4 OpenRouter Integration

**Existing Setup:**
```
Backend ENV: OPENAI_API_BASE_URL = https://openrouter.ai/api/v1
Backend ENV: OPENAI_API_KEY = ${OPENROUTER_API_KEY}
```

**Implementation:**
- Use existing OpenAI client (already configured)
- No changes needed to HTTP layer
- Function module calls standard `openai.ChatCompletion.create()`
- Model selection can be dynamic or fixed (e.g., `meta-llama/llama-3-8b-instruct:free`)

### 4.5 Frontend Integration

#### A) Triggering the Action
**Current Flow in OpenWebUI:**
```
User clicks message action button
  ↓
Frontend calls: POST /api/chat/actions/{action_id}
  ↓
Backend executes: function_module.action(body={...})
  ↓
Response displayed in chat
```

**For Learning Tutor:**
- Action appears in message context menu (automatically)
- User clicks "Learning Tutor" action on any message
- Payload includes: `model`, `chat_id`, `user_id`, `message_id`, `messages[]`

#### B) UI Display
No additional frontend changes needed. The action button appears naturally in the message toolbar.

Optional enhancement (not in V1):
- Add a persistent "Ask Tutor" button in the chat interface
- Button would be conditionally visible for users in learning mode

---

## 5. Implementation Blocks

### ✅ Block 1: Database Schema
- [x] Plan schema (`user_learning_progress`)
- [ ] Create migration (Alembic)
- [ ] Test with Docker Compose

### ✅ Block 2: Python Model & CRUD
- [x] Define SQLAlchemy model
- [x] Pydantic schema
- [ ] Create CRUD operations (create, read, update)
- [ ] Add to `backend/open_webui/models/__init__.py`

### ✅ Block 3: Prompts Infrastructure
- [x] Define directory structure
- [ ] Create prompt files (step_1.txt through step_6.txt)
- [ ] Create prompt loader utility (`load_prompt(step_id)`)

### ✅ Block 4: Learning Tutor Function
- [x] Design function module interface
- [ ] Implement `action()` function
- [ ] Implement OpenRouter API call
- [ ] Error handling & logging

### ✅ Block 5: Function Registration
- [x] Understand OpenWebUI function registration
- [ ] Register learning_tutor in DB
- [ ] Make accessible via admin panel

### ✅ Block 6: Testing
- [ ] Unit tests for CRUD operations
- [ ] Integration test with Docker Compose
- [ ] Manual test via OpenWebUI UI

---

## 6. Technology Stack: Missing vs. Existing

| Component | Status | Details |
|-----------|--------|---------|
| **FastAPI** | ✅ Exists | Used for all API routes |
| **PostgreSQL** | ✅ Exists | Docker Compose includes DB |
| **SQLAlchemy ORM** | ✅ Exists | All models use this pattern |
| **OpenAI Python Client** | ✅ Exists | For OpenRouter calls |
| **Svelte/SvelteKit** | ✅ Exists | Frontend framework |
| **Alembic** | ✅ Exists | DB migrations in place |
| **Pydantic** | ✅ Exists | Request/response validation |
| **.env Configuration** | ✅ Exists | `OPENROUTER_API_KEY` already supported |
| **Function Module System** | ✅ Exists | Plugin architecture in place |
| **OpenRouter Integration** | ✅ Exists | Already configured in docker-compose |

**Conclusion:** No missing technologies. All required infrastructure exists.

---

## 7. Consistency Matrix

### 7.1 Button → Prompts Consistency
- **Trigger:** User clicks "Learning Tutor" action
- **Lookup:** Backend queries `user_learning_progress.current_step` for that user
- **Match:** Load `/backend/open_webui/learning/prompts/step_{current_step}.txt`
- **Inject:** Merge system prompt + user context + user message
- **Result:** LLM respects pedagogical directive for that step

### 7.2 Prompts → BDD Consistency
- Prompts are text files (immutable, versioned in git)
- User state (`current_step`) stored in DB
- Mapping is deterministic: `step = current_step` → `prompts/step_{step}.txt`
- No race conditions if step is not modified during action execution

### 7.3 BDD → OpenRouter Consistency
- User object loaded from DB
- LLM call uses existing `OPENAI_API_BASE_URL` env
- Response streamed back to OpenWebUI
- No custom middleware needed

---

## 8. Acceptance Criteria Mapping

| Criterion | Implementation | Status |
|-----------|----------------|--------|
| Action Button visible in OpenWebUI | Automatic via Function registration | ✅ Design complete |
| Click triggers request | Native action system | ✅ Design complete |
| LLM response matches step_X.txt | Prompt injection in function module | ✅ Design complete |
| New users default to step 1 | CRUD with default value | ✅ Design complete |
| Request logged in FastAPI | Native logging (python logging) | ✅ Design complete |

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| User deletes/modifies prompt files | App breaks | Git versioning + validation in loader |
| Database migration fails | Deployment blocked | Test migrations in dev environment first |
| OpenRouter rate limiting | LLM calls fail | Add retry logic + error handling |
| Large response from LLM | UI rendering issues | Stream response, clip if > 2000 chars |
| User stuck at step | UX degradation | Manual step reset via admin panel |

---

## 10. Phase 2 Features (Backlog)

Not in V1, but planned:
- **Output Parsing:** Auto-increment step when LLM detects mastery
- **Multi-Model Selection:** Choose model per step
- **Concepts Tracking:** Store validated concepts in DB
- **Progress Visualization:** Show learning path completion %
- **Persistent Tutorial Button:** Always-visible button in chat
- **Step Branching:** Different paths based on user responses
- **Learning Analytics:** Dashboard for admin

---

## 11. Success Metrics

- [ ] Function appears in action menu within 2 clicks
- [ ] Response time < 2 seconds (excluding LLM latency)
- [ ] 100% of new users initialize at step 1
- [ ] Step progression is transparent in logs
- [ ] No database errors during concurrent access

---

## 12. Next Steps

1. **Confirm** this architecture with product team
2. **Create** Alembic migration for schema
3. **Implement** Block 1-2: Database layer
4. **Implement** Block 3: Prompt infrastructure
5. **Implement** Block 4-5: Function module
6. **Test** end-to-end in Docker Compose
7. **Document** admin setup instructions

---

## Appendix A: File Locations Reference

```
backend/
├── open_webui/
│   ├── models/
│   │   └── learning.py              (NEW: UserLearningProgress model)
│   ├── functions/
│   │   └── learning_tutor.py        (NEW: Tutor action function)
│   ├── learning/
│   │   └── prompts/
│   │       ├── step_1.txt           (NEW: Overview)
│   │       ├── step_2.txt           (NEW: Deep dive 1)
│   │       ├── step_3.txt           (NEW: Deep dive 2)
│   │       ├── step_4.txt           (NEW: Practice)
│   │       ├── step_5.txt           (NEW: Quiz)
│   │       └── step_6.txt           (NEW: Synthesis)
│   ├── migrations/
│   │   └── versions/
│   │       └── XXXX_add_learning_progress.py  (NEW: Alembic migration)
│   └── utils/
│       └── learning.py              (NEW: Prompt loader utility)
└── requirements.txt                 (No changes needed)

src/
└── lib/
    └── components/
        └── chat/                    (No frontend changes needed)
```

---

**Status:** Ready for implementation  
**Reviewed By:** [Awaiting user approval]
