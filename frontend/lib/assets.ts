import { apiUrl } from "./api-base";

export function staticFileUrl(path: string | null, kind: "audio" | "screenshots"): string | null {
  if (!path) return null;
  const file = path.replace(/^.*[/\\]/, "");
  if (!file) return null;
  return apiUrl(`/static/${kind}/${file}`);
}
