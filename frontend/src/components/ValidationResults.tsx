import type { ReportFormat, ValidationResult } from "../types/api";
import { clampQualityScore, formatQualityScore } from "../utils/format";
import { Icon } from "./Icons";
import { IssueTable } from "./IssueTable";
import { MetricCard } from "./MetricCard";

interface ValidationResultsProps {
  result: ValidationResult;
  downloading: ReportFormat | null;
  downloadError: string | null;
  onDownload: (format: ReportFormat) => void;
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

function scoreTone(score: number): string {
  if (score >= 90) return "excellent";
  if (score >= 75) return "good";
  if (score >= 50) return "attention";
  return "critical";
}

export function ValidationResults({
  result,
  downloading,
  downloadError,
  onDownload,
}: ValidationResultsProps) {
  const score = formatQualityScore(result.quality_score);
  const visualScore = clampQualityScore(result.quality_score);
  const tone = scoreTone(visualScore);

  return (
    <div className="results-stack">
      <section
        className="panel result-overview"
        aria-labelledby="validation-results-title"
      >
        <div className="result-overview__heading">
          <div>
            <p className="eyebrow">Validation complete</p>
            <h2 id="validation-results-title">{result.filename}</h2>
            <p>Completed {formatDate(result.created_at)}</p>
          </div>
          <div className="report-actions">
            <button
              className="button button--secondary"
              disabled={downloading !== null}
              onClick={() => onDownload("xlsx")}
              type="button"
            >
              <Icon name="download" />
              {downloading === "xlsx" ? "Preparing…" : "Download Excel"}
            </button>
            <button
              className="button button--dark"
              disabled={downloading !== null}
              onClick={() => onDownload("pdf")}
              type="button"
            >
              <Icon name="download" />
              {downloading === "pdf" ? "Preparing…" : "Download PDF"}
            </button>
          </div>
        </div>

        {downloadError && (
          <div className="inline-alert inline-alert--error" role="alert">
            <Icon name="warning" />
            <span>{downloadError}</span>
          </div>
        )}

        <div className="score-layout">
          <article className={`score-card score-card--${tone}`}>
            <div
              aria-label={`Quality score: ${score} out of 100`}
              className="score-ring"
              style={{ "--score": `${visualScore * 3.6}deg` } as React.CSSProperties}
            >
              <div>
                <strong>{score}</strong>
                <span>/ 100</span>
              </div>
            </div>
            <div>
              <span className="score-card__label">Quality score</span>
              <strong>
                {tone === "excellent"
                  ? "Excellent"
                  : tone === "good"
                    ? "Good"
                    : tone === "attention"
                      ? "Needs attention"
                      : "Action required"}
              </strong>
              <p>Calculated by the validation service from this file.</p>
            </div>
          </article>

          <div className="metrics-grid">
            <MetricCard
              hint={`${result.metrics.valid_rows.toLocaleString()} valid`}
              label="Rows checked"
              value={result.metrics.total_rows}
            />
            <MetricCard
              hint="Require correction"
              label="Errors"
              tone="negative"
              value={result.metrics.error_count}
            />
            <MetricCard
              hint="Need review"
              label="Warnings"
              tone="warning"
              value={result.metrics.warning_count}
            />
            <MetricCard
              hint="Informational"
              label="Information"
              tone="info"
              value={result.metrics.info_count}
            />
          </div>
        </div>
      </section>

      <IssueTable
        issueCount={result.metrics.issue_count}
        issues={result.issues}
        issuesTruncated={result.metrics.issues_truncated}
      />
    </div>
  );
}
