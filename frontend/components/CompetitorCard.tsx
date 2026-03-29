export function CompetitorCard({
  name,
  rating,
  review_count,
}: {
  name: string;
  rating?: number | null;
  review_count?: number | null;
}) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-card/50 p-4 backdrop-blur-sm transition hover:border-white/[0.1]">
      <p className="font-medium text-white">{name}</p>
      <p className="mt-2 text-[12px] text-zinc-500">
        {rating != null ? <span className="text-zinc-300">★ {rating}</span> : "—"}
        <span className="text-zinc-700"> · </span>
        {review_count ?? 0} reviews
      </p>
    </div>
  );
}
