export type SmbFit = {
  target_tier?: string;
  chain_likelihood?: number;
  simplicity_score?: number;
  fixability_score?: number;
  smb_fit_index?: number;
  reasons?: string[];
};

export type AiEasyWin = {
  fix?: string;
  why_it_matters?: string;
  effort?: string;
  how_you_fix_it?: string;
};

export type AiSmbIntel = {
  easy_wins?: AiEasyWin[];
  chain_verdict?: string;
  ideal_client_for_solo_dev?: boolean;
  tech_simplicity_note?: string;
  what_not_to_sell?: string;
};

export type SiteIntel = {
  archetype?: string;
  static_affinity?: number;
  spa_risk?: number;
  spa_marker_hits?: number;
};

export type LeadFeatures = {
  smb_fit?: SmbFit;
  ai_smb_intel?: AiSmbIntel;
  site_intel?: SiteIntel;
  builder?: string;
  [key: string]: unknown;
};

export type Lead = {
  id: number;
  place_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  business_name: string;
  category: string | null;
  address: string | null;
  city?: string | null;
  phone: string | null;
  website: string | null;
  google_rating: number | null;
  review_count: number | null;
  no_website?: boolean | null;
  scrape_error?: string | null;
  load_time_ms?: number | null;
  last_analyzed_at?: string | null;
  email_pitch?: string | null;
  lead_score: number | null;
  revenue_opportunity_monthly: number | null;
  revenue_opportunity_desc: string | null;
  status: string;
  source: string;
  ai_summary: string | null;
  ai_pitch: string | null;
  ai_urgency_reason?: string | null;
  ai_biggest_problem: string | null;
  ai_recommended_service: string | null;
  ai_estimated_value: string | null;
  call_script: string | null;
  competitors: unknown[] | null;
  competitive_gaps: string[] | null;
  issues: { severity: string; title: string; description?: string; impact?: number }[] | null;
  pagespeed_mobile: number | null;
  pagespeed_desktop: number | null;
  pagespeed_opportunities?: { id?: string; title?: string; description?: string }[] | null;
  desktop_screenshot_path: string | null;
  mobile_screenshot_path: string | null;
  audio_briefing_path: string | null;
  opportunity_score: number | null;
  technical_debt_score: number | null;
  urgency_score: number | null;
  seo_score: number | null;
  mobile_score: number | null;
  content_score: number | null;
  notes: string | null;
  features?: LeadFeatures | null;
};

export type Stats = {
  total_leads: number;
  new_this_week: number;
  total_monthly_opportunity: number;
  avg_lead_score: number;
  pending_analysis?: number;
};
