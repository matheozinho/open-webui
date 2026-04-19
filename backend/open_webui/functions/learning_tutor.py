import os
import json
import requests
from sqlalchemy.orm import Session

# Imports internes à Open WebUI
from open_webui.internal.db import get_db
from open_webui.models.learning import UserLearningProgress
from open_webui.learning.prompt_loader import load_prompt

class Tools:
    def __init__(self):
        pass

    def action(
        self, body: dict, __user__: dict = None, __event_emitter__: callable = None
    ):
        # --- CORRECTIF : Gestion du body si c'est une string ---
        if isinstance(body, str):
            user_message_from_body = body
            model_id = "openrouter/auto"
            full_body = {}
        else:
            user_message_from_body = ""
            model_id = body.get("model", "openrouter/auto")
            full_body = body

        user_id = __user__.get("id")

        # 1. Recherche du message utilisateur ultra-robuste
        user_message = (
            user_message_from_body
            or full_body.get("user_message")
            or full_body.get("message", {}).get("content")
            or full_body.get("content")
            or ""
        )

        # Secours historique (clé 'messages')
        if (
            not user_message
            and "messages" in full_body
            and isinstance(full_body["messages"], list)
        ):
            for msg in reversed(full_body["messages"]):
                if msg.get("role") == "user" and msg.get("content"):
                    user_message = msg["content"]
                    break

        # 2. Accès BDD
        try:
            db: Session = next(get_db())
            progress = db.query(UserLearningProgress).filter_by(user_id=user_id).first()
            step = progress.current_step if progress else 1
        except Exception:
            step = 1

        # 3. Chargement du Prompt
        try:
            system_prompt = load_prompt(step)
        except Exception:
            system_prompt = f"Tu es un tuteur expert. Étape {step}. Aide l'utilisateur."

        # 4. Appel OpenRouter
        api_key = os.getenv("OPENROUTER_API_KEY")
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }

        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            answer = result["choices"][0]["message"]["content"]

            debug_json = {
                "user_id": user_id,
                "step": step,
                "user_message": user_message,
                "system_prompt": system_prompt,
                "payload": payload,
                "llm_response": answer
            }

            return (
                answer
                + "\n\n---\n**PAYLOAD ENVOYÉ AU LLM :**\n```json\n"
                + json.dumps(payload, ensure_ascii=False, indent=2)
                + "\n```\n"
                + "**DEBUG COMPLET :**\n```json\n"
                + json.dumps(debug_json, ensure_ascii=False, indent=2)
                + "\n```"
            )

        except Exception as e:
            return f"Erreur lors de l'appel au tuteur : {str(e)}"