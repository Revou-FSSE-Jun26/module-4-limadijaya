import type { Analytics } from "@/types/api";

export interface AnalyticsPanelProps {
  analytics: Analytics | null;
  error: string | null;
}

function day(iso: string): string {
  return iso.slice(0, 10);
}

/** Weekly analytics from the API. The week is UTC and the end date is exclusive (FRONT-007). */
export default function AnalyticsPanel({ analytics, error }: AnalyticsPanelProps) {
  return (
    <section aria-labelledby="analytics-title" className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 id="analytics-title" className="text-base font-semibold text-slate-900">
        Board analytics
      </h2>
      {error ? (
        <p role="alert" className="mt-2 text-sm text-red-700">
          Analytics could not be loaded: {error}
        </p>
      ) : null}
      {analytics ? (
        <div className="mt-3 space-y-4 text-sm text-slate-700">
          <p>
            Week (UTC): {day(analytics.window.start)} to {day(analytics.window.end)} (end not included)
          </p>
          {analytics.cards_per_column.length === 0 ? (
            <p>This board has no columns yet.</p>
          ) : (
            <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {analytics.cards_per_column.map((column) => (
                <li key={column.column_id} className="flex justify-between rounded bg-slate-50 px-3 py-2">
                  <span className="truncate">{column.name}</span>
                  <span className="font-semibold">{column.card_count}</span>
                </li>
              ))}
            </ul>
          )}
          <p>
            Cards completed this week: <span className="font-semibold">{analytics.completed_this_week}</span>
          </p>
          <div>
            <h3 className="font-medium text-slate-900">Member activity</h3>
            <ul className="mt-1 space-y-1">
              {analytics.member_activity.map((member) => (
                <li key={member.user_id} className="flex justify-between">
                  <span>{member.name}</span>
                  <span className="font-semibold">{member.activity_count}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </section>
  );
}