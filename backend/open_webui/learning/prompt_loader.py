import os

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def load_prompt(step: int) -> str:
    """Charge le texte du prompt pour l'étape donnée."""
    path = os.path.join(PROMPT_DIR, f"step_{step}.txt")
    print(f"DEBUG: Chargement du prompt {path}")
    if not os.path.isfile(path):
        print("DEBUG: Fichier non trouvé, fallback.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        print("DEBUG: Contenu du prompt:", content)
        return content
