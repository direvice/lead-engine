/** External links for a lead row / dossier (maps, website). */

export function normalizeWebsiteUrl(raw: string | null | undefined): string | null {
  if (!raw?.trim()) return null;
  const t = raw.trim();
  if (t.startsWith("http://") || t.startsWith("https://")) return t;
  return `https://${t}`;
}

export function googleMapsUrl(lead: {
  place_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  address?: string | null;
  business_name?: string | null;
}): string | null {
  if (lead.place_id) {
    return `https://www.google.com/maps/search/?api=1&query_place_id=${encodeURIComponent(lead.place_id)}`;
  }
  if (lead.latitude != null && lead.longitude != null) {
    return `https://www.google.com/maps?q=${lead.latitude},${lead.longitude}`;
  }
  const q = [lead.business_name, lead.address].filter(Boolean).join(", ").trim();
  if (!q) return null;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`;
}

export function googleSearchUrl(businessName: string, address?: string | null): string {
  const q = [businessName, address].filter(Boolean).join(" ").trim();
  return `https://www.google.com/search?q=${encodeURIComponent(q)}`;
}
