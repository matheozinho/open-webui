from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from open_webui.internal.db import get_db
from open_webui.models.learning import UserLearningProgress
from open_webui.learning.prompt_loader import load_prompt

router = APIRouter()

@router.get("/learning/prompt/{user_id}")
def get_learning_prompt(user_id: str, db: Session = Depends(get_db)):
    progress = (
        db.query(UserLearningProgress)
        .filter(UserLearningProgress.user_id == user_id)
        .first()
    )
    if progress:
        step = progress.current_step
    else:
        step = 1
    prompt_txt = load_prompt(step)
    if not prompt_txt:
        if step == 1:
            prompt_txt = "1. Contextualisation du Sujet\n\nObjectif : Situé le sujet dans son contexte temporel et identifier les enjeux majeurs.\n\nActions :\n\nFournir une vue d'ensemble historique ou temporelle.\n\nIdentifier les événements clés et les acteurs principaux.\n\nUtiliser des visualisations ou des chronologies pour mieux comprendre les relations entre les événements."
        else:
            raise HTTPException(status_code=500, detail=f"Prompt file for step {step} not found")
    system_prompt = (
        f"[SYSTEM]\n"
        f"User: {user_id}\n"
        f"Current step: {step}\n"
        f"Prompt instructions:\n{prompt_txt}\n"
        f"[/SYSTEM]"
    )
    return {
        "user_id": user_id,
        "current_step": step,
        "system_prompt": system_prompt
    }
