"""
Memory Bridge Module for UIMA (User Identity & Memory Architecture)
Injects user profile context into chat messages before processing
"""

import logging
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)


class MemoryBridge:
    """
    Bridge between user profiles and chat system.
    Dynamically injects user context into chat messages.
    """

    @staticmethod
    def get_user_context(user) -> Optional[Dict[str, Any]]:
        """
        Fetch user profile and return context dictionary
        """
        try:
            # Lazy import to avoid circular imports
            from open_webui.models.user_profiles import UserProfiles
            
            profile = UserProfiles.get_profile_by_user_id(user.id)
            if profile is None:
                log.debug(f"No profile found for user {user.id}")
                return None

            return {
                "user_id": user.id,
                "username": user.username or user.name,
                "job": profile.job,
                "tone_preference": profile.tone_preference,
                "project_context": profile.project_context,
                "preferences": profile.preferences or {},
            }
        except Exception as e:
            log.error(f"Error fetching user context: {e}")
            return None

    @staticmethod
    def build_context_prompt(user_context: Dict[str, Any]) -> str:
        """
        Build a system prompt injection from user context
        """
        if not user_context:
            return ""

        context_parts = []

        if user_context.get("username"):
            context_parts.append(f"User: {user_context['username']}")

        if user_context.get("job"):
            context_parts.append(f"Job/Role: {user_context['job']}")

        if user_context.get("tone_preference"):
            context_parts.append(f"Communication Tone: {user_context['tone_preference']}")

        if user_context.get("project_context"):
            context_parts.append(f"Project Context:\n{user_context['project_context']}")

        if not context_parts:
            return ""

        prompt = "## User Profile Context\n"
        prompt += "\n".join(context_parts)
        prompt += "\n\nPlease tailor your responses considering the user's profile above."

        return prompt

    @staticmethod
    def inject_user_context_to_messages(
        messages: list, user
    ) -> list:
        """
        Inject user profile context into the system message of messages list
        """
        if not messages:
            return messages

        user_context = MemoryBridge.get_user_context(user)
        if not user_context:
            return messages

        context_prompt = MemoryBridge.build_context_prompt(user_context)
        if not context_prompt:
            return messages

        # Find or create system message
        system_message_idx = None
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                system_message_idx = i
                break

        if system_message_idx is not None:
            # Append context to existing system message
            messages[system_message_idx]["content"] = (
                f"{messages[system_message_idx].get('content', '')}\n\n{context_prompt}"
            )
        else:
            # Create new system message at the beginning
            messages.insert(
                0, {"role": "system", "content": context_prompt}
            )

        return messages

    @staticmethod
    def inject_context_to_form_data(form_data: dict, user) -> dict:
        """
        Inject user context into form_data (chat completion request)
        """
        if "messages" not in form_data:
            return form_data

        form_data["messages"] = MemoryBridge.inject_user_context_to_messages(
            form_data["messages"], user
        )

        return form_data
