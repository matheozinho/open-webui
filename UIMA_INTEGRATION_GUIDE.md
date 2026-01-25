"""
UIMA Memory Bridge Integration Example
This file shows how to integrate the Memory Bridge into the OpenAI chat completion endpoint
"""

# LOCATION: backend/open_webui/routers/openai.py
# This is example code showing integration points

# ============================================================================
# INTEGRATION EXAMPLE 1: Basic Integration in Chat Completion
# ============================================================================

# At the top of the file, add this import:
"""
from open_webui.utils.memory_bridge import MemoryBridge
"""

# In the chat completion endpoint (around line 700-900), add this before sending to model:
"""
@router.post("/chat/completions")
async def chat_completion(request: Request, form_data: dict, user=Depends(get_verified_user)):
    # ... existing code ...
    
    # INJECT USER CONTEXT BEFORE COMPLETION
    form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
    
    # ... rest of completion logic ...
    # Send enriched form_data to model
"""

# ============================================================================
# INTEGRATION EXAMPLE 2: With Custom Handlers
# ============================================================================

"""
If you need more control, use the low-level functions:

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
"""

# ============================================================================
# INTEGRATION EXAMPLE 3: With Logging
# ============================================================================

"""
For debugging, add logging:

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
"""

# ============================================================================
# STEP-BY-STEP INTEGRATION INSTRUCTIONS
# ============================================================================

"""
1. LOCATE THE CHAT COMPLETION ENDPOINT
   File: backend/open_webui/routers/openai.py
   Search for: "def chat_completion" or "@router.post"
   
2. ADD IMPORT AT TOP
   from open_webui.utils.memory_bridge import MemoryBridge
   
3. FIND CHAT COMPLETION HANDLER
   Look for where messages are prepared before sending to LLM model
   This is typically before:
   - aiohttp requests
   - requests.post calls
   - form_data modifications
   
4. ADD CONTEXT INJECTION
   # Get user from request
   user = get_verified_user(...)
   
   # Inject context
   if user:
       form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
   
5. TEST
   - Create a user with a profile
   - Send a chat message
   - Check if system message includes profile context
   - Monitor logs for debug output

6. VERIFY IN ADMINER
   - Go to http://localhost:8081
   - Check user_profiles table
   - Ensure user_id matches authenticated user
"""

# ============================================================================
# TESTING THE INTEGRATION
# ============================================================================

"""
AUTOMATED TEST EXAMPLE:

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
"""

# ============================================================================
# OPTIONAL: CONDITIONAL CONTEXT INJECTION
# ============================================================================

"""
You can make context injection conditional based on model or settings:

async def chat_completion(...):
    # Only inject context for certain models
    if form_data.get("model") in ["gpt-4", "claude-3"]:
        form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
    
    # Or check if user has context injection enabled
    user_settings = UserSettings.get_settings(user.id)
    if user_settings.enable_memory_bridge:
        form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
"""

# ============================================================================
# MONITORING & METRICS
# ============================================================================

"""
Track Memory Bridge usage:

class MemoryBridgeMetrics:
    profiles_injected = 0
    profiles_not_found = 0
    errors = 0
    
    @classmethod
    def record_injection(cls, success: bool):
        if success:
            cls.profiles_injected += 1
        else:
            cls.profiles_not_found += 1

# Use in integration:
context = MemoryBridge.get_user_context(user)
if context:
    MemoryBridgeMetrics.record_injection(True)
    form_data = MemoryBridge.inject_context_to_form_data(form_data, user)
else:
    MemoryBridgeMetrics.record_injection(False)
"""

# ============================================================================
# API EXAMPLE FLOW
# ============================================================================

"""
CURL EXAMPLE:

1. Login to get token:
curl -X POST http://localhost:3000/api/v1/auths/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
  
Response: {"token": "eyJ0eXAiOiJKV1QiLCJhbGc..."}

2. Create user profile:
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

curl -X POST http://localhost:3000/api/v1/user-profiles/profiles/user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job": "Software Engineer",
    "tone_preference": "technical",
    "project_context": "Building a REST API with FastAPI"
  }'

3. Send chat message (with context injection):
curl -X POST http://localhost:3000/openai/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Help me optimize this API endpoint"}
    ]
  }'

Response will include system message with your profile context!
"""

# ============================================================================
# TROUBLESHOOTING INTEGRATION
# ============================================================================

"""
COMMON ISSUES:

1. "MemoryBridge module not found"
   - Verify file exists: backend/open_webui/utils/memory_bridge.py
   - Restart backend: docker-compose restart open-webui

2. "Profile not being injected"
   - Check user is logged in (has valid token)
   - Verify profile exists in database: SELECT * FROM user_profiles;
   - Enable debug logging: GLOBAL_LOG_LEVEL=DEBUG

3. "System message not showing in response"
   - Check if LLM supports system messages (most do)
   - Verify message format is correct (role: "system")
   - Some models filter out system messages from responses

4. "Performance issues with context injection"
   - Add database query caching (Redis)
   - Use connection pooling
   - Consider indexing user_id (already done)
"""
