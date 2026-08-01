import type { ValidationSummary } from "../types/api";
import { formatQualityScore } from "../utils/format";
import { Icon } from "./Icons";

interface RecentValidationsProps {
  items: ValidationSummary[];
  loading: boolean;
  error: string | null;
  openingId: string | null;
  onOpen: (id: string) => void;
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
}

function qualityTone(score: number): string {
  if (score >= 90) return "high";
  if (score >= 75) return "medium";
  return "low";
}

export function RecentValidations({
  items,
  loading,
  error,
  openingId,
  onOpen,
}: RecentValidationsProps) {
  return (
    <section className="panel recent-panel" aria-labelledby="recent-title">
      <div className="panel__header recent-header">
        <div>
          <p className="eyebrow">History</p>
          <h2 id="recent-title">Recent validations</h2>
          <p>Reopen a previous validation returned by the service.</p>
        </div>
        <Icon name="clock" />
      </div>

      {loading ? (
        <div className="recent-loading" aria-label="Loading recent validations">
          <span />
          <span />
          <span />
        </div>
      ) : error ? (
        <div className="quiet-state">
          <Icon name="info" />
          <div>
            <strong>History is unavailable</strong>
            <p>{error}</p>
          </div>
        </div>
      ) : items.length === 0 ? (
        <div className="quiet-state">
          <Icon name="file" />
          <div>
            <strong>No validations yet</strong>
            <p>Completed runs will appear here.</p>
          </div>
        </div>
      ) : (
        <div className="recent-list">
          {items.map((item) => (
            <button
              className="recent-item"
              disabled={openingId !== null}
              key={item.id}
              onClick={() => onOpen(item.id)}
              type="button"
            >
              <span className="recent-item__file">
                <span>
                  <Icon name="file" />
                </span>
                <span>
                  <strong title={item.filename}>{item.filename}</strong>
                  <small>{formatDate(item.created_at)}</small>
                </span>
              </span>
              <span className="recent-item__meta">
                <span
                  className={`quality-pill quality-pill--${qualityTone(item.quality_score)}`}
                >
                  {formatQualityScore(item.quality_score)}
                </span>
                <span>
                  {item.metrics.issue_count.toLocaleString()}{" "}
                  {item.metrics.issue_count === 1 ? "issue" : "issues"}
                </span>
                {openingId === item.id ? (
                  <span className="mini-spinner" aria-label="Opening validation" />
                ) : (
                  <Icon name="chevron-right" />
                )}
              </span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
