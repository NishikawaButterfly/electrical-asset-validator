import { useState } from "react";
import type { ComparisonResult } from "../types/api";
import { Icon } from "./Icons";
import { MetricCard } from "./MetricCard";

type ChangeView = "changed" | "added" | "removed";

interface ComparisonResultsProps {
  result: ComparisonResult;
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

function formatValue(value: string | number | boolean | null): string {
  if (value === null || value === "") return "Empty";
  return String(value);
}

export function ComparisonResults({ result }: ComparisonResultsProps) {
  const [view, setView] = useState<ChangeView>("changed");

  return (
    <div className="results-stack">
      <section className="panel" aria-labelledby="comparison-results-title">
        <div className="panel__header comparison-heading">
          <div>
            <p className="eyebrow">Comparison complete</p>
            <h2 id="comparison-results-title">Revision summary</h2>
            <p>Compared {formatDate(result.created_at)}</p>
          </div>
          <div className="revision-pair" aria-label="Files compared">
            <span title={result.before_filename}>{result.before_filename}</span>
            <Icon name="arrow-right" />
            <span title={result.after_filename}>{result.after_filename}</span>
          </div>
        </div>

        <div className="comparison-metrics">
          <MetricCard
            hint="Only in the new revision"
            label="Added"
            tone="positive"
            value={result.summary.added}
          />
          <MetricCard
            hint="Missing from the new revision"
            label="Removed"
            tone="negative"
            value={result.summary.removed}
          />
          <MetricCard
            hint="Fields differ"
            label="Changed"
            tone="warning"
            value={result.summary.changed}
          />
          <MetricCard
            hint="No detected differences"
            label="Unchanged"
            value={result.summary.unchanged}
          />
        </div>
      </section>

      <section className="panel comparison-details" aria-labelledby="changes-title">
        <div className="panel__header">
          <div>
            <p className="eyebrow">Revision detail</p>
            <h2 id="changes-title">What changed</h2>
            <p>Inspect assets and field-level differences between the two files.</p>
          </div>
        </div>

        <div className="change-tabs" role="tablist" aria-label="Change category">
          {(["changed", "added", "removed"] as const).map((category) => (
            <button
              aria-controls={`change-panel-${category}`}
              aria-selected={view === category}
              className={view === category ? "change-tab change-tab--active" : "change-tab"}
              id={`change-tab-${category}`}
              key={category}
              onClick={() => setView(category)}
              role="tab"
              type="button"
            >
              {category[0].toUpperCase() + category.slice(1)}
              <span>
                {category === "changed"
                  ? result.summary.changed
                  : category === "added"
                    ? result.summary.added
                    : result.summary.removed}
              </span>
            </button>
          ))}
        </div>

        <div
          aria-labelledby={`change-tab-${view}`}
          className="change-panel"
          id={`change-panel-${view}`}
          role="tabpanel"
        >
          {view === "changed" &&
            (result.changed.length > 0 ? (
              <div className="changed-list">
                {result.changed.map((asset) => (
                  <article className="changed-asset" key={asset.asset_tag}>
                    <header>
                      <span>Asset</span>
                      <strong>{asset.asset_tag}</strong>
                      <span className="count-badge">
                        {asset.changes.length}{" "}
                        {asset.changes.length === 1 ? "field" : "fields"}
                      </span>
                    </header>
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>Field</th>
                            <th>Before</th>
                            <th aria-label="Direction" />
                            <th>After</th>
                          </tr>
                        </thead>
                        <tbody>
                          {asset.changes.map((change, index) => (
                            <tr key={`${change.field}-${index}`}>
                              <td>
                                <code>{change.field}</code>
                              </td>
                              <td className="diff-value diff-value--before">
                                {formatValue(change.before)}
                              </td>
                              <td className="diff-arrow">
                                <Icon name="arrow-right" />
                              </td>
                              <td className="diff-value diff-value--after">
                                {formatValue(change.after)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <ChangeEmpty label="changed assets" />
            ))}

          {view === "added" &&
            (result.added.length > 0 ? (
              <AssetChangeTable assets={result.added} kind="added" />
            ) : (
              <ChangeEmpty label="added assets" />
            ))}

          {view === "removed" &&
            (result.removed.length > 0 ? (
              <AssetChangeTable assets={result.removed} kind="removed" />
            ) : (
              <ChangeEmpty label="removed assets" />
            ))}
        </div>
      </section>
    </div>
  );
}

function AssetChangeTable({
  assets,
  kind,
}: {
  assets: ComparisonResult["added"];
  kind: "added" | "removed";
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Asset tag</th>
            <th>Source row</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {assets.map((asset, index) => (
            <tr key={`${asset.asset_tag}-${asset.row}-${index}`}>
              <td>
                <strong className="asset-tag">{asset.asset_tag}</strong>
              </td>
              <td>{asset.row}</td>
              <td>
                <span className={`change-badge change-badge--${kind}`}>
                  {kind}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChangeEmpty({ label }: { label: string }) {
  return (
    <div className="table-empty">
      <span>
        <Icon name="check" />
      </span>
      <strong>No {label} were returned</strong>
      <p>The comparison service did not report items in this category.</p>
    </div>
  );
}
