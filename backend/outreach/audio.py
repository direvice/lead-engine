"""gTTS audio briefings."""

from __future__ import annotations

import os
import re

from gtts import gTTS

from config import get_settings


def _speak_phone(phone: str | None) -> str:
    if not phone:
        return "unknown"
    digits = re.sub(r"\D", "", phone)
    return " ".join(digits) if digits else phone


def generate_audio_briefing(lead_id: int, lead: dict) -> str:
    settings = get_settings()
    os.makedirs(settings.audio_dir, exist_ok=True)
    path = os.path.join(settings.audio_dir, f"{lead_id}.mp3")
    text = f"""
Lead briefing for {lead.get('business_name')}.
Located at {lead.get('address') or 'unknown address'}.
Phone number: {_speak_phone(lead.get('phone'))}.
Lead score: {lead.get('lead_score')} out of 100.
Opportunity: approximately {lead.get('revenue_opportunity_monthly') or 0} dollars per month.
Biggest problem: {lead.get('ai_biggest_problem') or 'see dashboard'}.
Pitch angle: {lead.get('ai_pitch') or ''}.
Recommended service: {lead.get('ai_recommended_service') or ''}.
Estimated project value: {lead.get('ai_estimated_value') or ''}.
    """.strip()
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(path)
    return path
