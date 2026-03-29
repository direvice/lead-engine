"""Prompt templates for free/local models."""

ANALYSIS_PROMPT = """You are a web development sales analyst.
Analyze this local business website audit and respond with
ONLY valid JSON matching this exact schema:

{{
  "summary": "2-3 sentences about their website situation",
  "biggest_problem": "single most critical issue",
  "pitch_angle": "one sentence on how to open the sales call",
  "recommended_service": "one of: [Website fixes, Custom website, Web app, SaaS build, AI automation, Monthly retainer]",
  "estimated_value": "dollar range like $2500-$4500",
  "revenue_opportunity": "specific dollar amount they're losing monthly",
  "urgency_reason": "why they need this now specifically"
}}

Business data:
Name: {name}
Type: {category}
City: {city}
Google rating: {rating} ({reviews} reviews)
Website builder: {builder}
Critical issues: {critical_issues}
Missing features: {missing_features}
Monthly revenue opportunity: ${opportunity_calc}

Respond with JSON only. No explanation."""

JSON_RETRY_SUFFIX = "\n\nYour previous response was not valid JSON. Reply with ONLY a single JSON object, no markdown fences."

CLASSIFY_PROMPT = """Pick exactly one option from this list by replying with only the option text, nothing else:
Options: {options}

Text to classify:
{text}
"""

PITCH_PROMPT = """Write a short, professional cold email (under 180 words) for a local web developer
offering help to this business. Use their situation. End with a soft CTA.

Business: {name}
Category: {category}
City: {city}
Summary: {summary}
Biggest problem: {biggest_problem}
Pitch angle: {pitch_angle}
Revenue opportunity note: {revenue_note}

Reply with ONLY valid JSON: {{"subject": "...", "body": "..."}}"""
