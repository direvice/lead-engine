import type { Lead } from "@/lib/types";

const severityOrder = ["critical", "high", "medium", "low"];

export function IssueList({ issues }: { issues: Lead["issues"] }) {
  if (!issues?.length) {
    return <p className="text-[13px] text-zinc-600">No structured issues for this lead.</p>;
  }
  const grouped: Record<string, NonNullable<Lead["issues"]>> = {};
  issues.forEach((i) => {
    const s = i.severity || "low";
    grouped[s] = grouped[s] || [];
    grouped[s]!.push(i);
  });

  return (
    <div className="space-y-8">
      {severityOrder.map((sev) => {
        const list = grouped[sev];
        if (!list?.length) return null;
        return (
          <div key={sev}>
            <h4 className="text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-600">{sev}</h4>
            <ul className="mt-3 space-y-2">
              {list.map((issue, idx) => (
                <li
                  key={idx}
                  className="rounded-xl border border-white/[0.05] bg-white/[0.02] px-4 py-3"
                >
                  <p className="text-[14px] font-medium text-zinc-200">{issue.title}</p>
                  {issue.description ? (
                    <p className="mt-1 text-[13px] leading-relaxed text-zinc-500">{issue.description}</p>
                  ) : null}
                  {issue.impact != null ? (
                    <p className="mt-2 text-[11px] text-zinc-600">Impact · −{issue.impact}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
