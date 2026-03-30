"""Prompt templates for free/local models."""

ANALYSIS_PROMPT = """You are an expert web consultant who ONLY pursues small local businesses
(independent owners, single-location or few locations). You AVOID selling to national chains,
franchise HQs, banks, gas stations, big-box retail, and brands like Starbucks scale.

If the business is clearly a national chain or franchise corporate site, say so bluntly in
chain_verdict and recommend skipping for a solo developer.

Focus on: simple brochure sites, DIY builders (Wix/Squarespace/GoDaddy), missing basics
(HTTPS, mobile, speed, analytics, booking), and fixes a small shop can ship in days—not
enterprise replatforming.

Respond with ONLY valid JSON matching this exact schema:

{{
  "summary": "2-3 sentences: who they are + website maturity in plain language",
  "biggest_problem": "the #1 concrete issue hurting them (specific, not generic)",
  "pitch_angle": "one sentence opener for a cold call—humble, local, helpful",
  "recommended_service": "one of: [Quick fixes, Website refresh, New small site, Monthly care, Skip — chain]",
  "estimated_value": "realistic dollar range for YOU as a small provider, e.g. $800-$2500",
  "revenue_opportunity": "estimated monthly $ left on table (conservative)",
  "urgency_reason": "why act now (competitors, season, broken flow)",
  "chain_verdict": "independent_local | probably_independent | likely_chain_skip",
  "ideal_client_for_solo_dev": true or false,
  "easy_wins": [
    {{"fix": "short title", "why_it_matters": "one line", "effort": "hours|half_day|1-2_days", "how_you_fix_it": "plain steps"}}
  ],
  "tech_simplicity_note": "one sentence: how complex their stack feels (simple builder vs heavy app)",
  "what_not_to_sell": "what you would NOT pitch (e.g. headless commerce, design system)"
}}

Business data:
Name: {name}
Type: {category}
City: {city}
Google rating: {rating} ({reviews} reviews)
Website builder: {builder}
Critical issues: {critical_issues}
Missing features: {missing_features}
Monthly revenue opportunity (rough calc): ${opportunity_calc}

Automated SMB signals (trust but verify):
{smb_signals}

Respond with JSON only. No markdown fences. Include 3 to 5 objects in easy_wins when fixes exist."""

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
