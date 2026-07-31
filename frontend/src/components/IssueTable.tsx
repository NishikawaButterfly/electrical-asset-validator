import { useMemo, useState } from "react";
import type { IssueSeverity, ValidationIssue } from "../types/api";
import { Icon } from "./Icons";

const PAGE_SIZE = 15;
type SeverityFilter = "all" | IssueSeverity;

interface IssueTableProps {
  issueCount: number;
  issues: ValidationIssue[];
  issuesTruncated: boolean;
}

function includesSearch(issue: ValidationIssue, search: string): boolean {
  const searchable = [
    issue.severity,
    issue.rule,
    issue.row,
    issue.asset_tag,
    issue.field,
    issue.message,
    issue.suggestion,
  ]
    .filter((value) => value !== null)
    .join(" ")
    .toLowerCase();

  return searchable.includes(search);
}

export function IssueTable({
  issueCount,
  issues,
  issuesTruncated,
}: IssueTableProps) {
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState<SeverityFilter>("all");
  const [page, setPage] = useState(1);

  const filteredIssues = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return issues.filter(
      (issue) =>
        (severity === "all" || issue.severity === severity) &&
        (!normalizedSearch || includesSearch(issue, normalizedSearch)),
    );
  }, [issues, search, severity]);

  const pageCount = Math.max(1, Math.ceil(filteredIssues.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const visibleIssues = filteredIssues.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE,
  );

  return (
    <section className="panel issues-panel" aria-labelledby="issues-title">
      <div className="panel__header issue-header">
        <div>
          <p className="eyebrow">Findings</p>
          <h2 id="issues-title">Validation issues</h2>
          <p>
            Review every reported issue and its suggested next action.
          </p>
        </div>
        <span className="count-badge">
          {issuesTruncated
            ? `${issues.length.toLocaleString()} shown`
            : `${issueCount.toLocaleString()} total`}
        </span>
      </div>

      {issuesTruncated && (
        <div className="issue-limit-note" role="status">
          <Icon name="info" />
          <span>
            Showing a bounded set of {issueCount.toLocaleString()} detected
            issues. Correct the listed findings and run validation again.
          </span>
        </div>
      )}

      <div className="issue-toolbar">
        <label className="search-field">
          <span className="sr-only">Search validation issues</span>
          <Icon name="search" />
          <input
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder="Search rule, asset, or message"
            type="search"
            value={search}
          />
        </label>
        <label className="select-field">
          <span className="sr-only">Filter by severity</span>
          <select
            onChange={(event) => {
              setSeverity(event.target.value as SeverityFilter);
              setPage(1);
            }}
            value={severity}
          >
            <option value="all">All severities</option>
            <option value="error">Errors</option>
            <option value="warning">Warnings</option>
            <option value="info">Information</option>
          </select>
        </label>
      </div>

      {visibleIssues.length > 0 ? (
        <>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Rule</th>
                  <th>Row</th>
                  <th>Asset</th>
                  <th>Message</th>
                  <th>Suggestion</th>
                </tr>
              </thead>
              <tbody>
                {visibleIssues.map((issue) => (
                  <tr key={issue.id}>
                    <td>
                      <span
                        className={`severity-badge severity-badge--${issue.severity}`}
                      >
                        <span aria-hidden="true" />
                        {issue.severity}
                      </span>
                    </td>
                    <td>
                      <code>{issue.rule}</code>
                      {issue.field && (
                        <small className="table-subtext">{issue.field}</small>
                      )}
                    </td>
                    <td>{issue.row ?? "—"}</td>
                    <td>
                      {issue.asset_tag ? (
                        <strong className="asset-tag">{issue.asset_tag}</strong>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="message-cell">{issue.message}</td>
                    <td className="suggestion-cell">
                      {issue.suggestion ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-footer">
            <span>
              Showing {(safePage - 1) * PAGE_SIZE + 1}–
              {Math.min(safePage * PAGE_SIZE, filteredIssues.length)} of{" "}
              {filteredIssues.length}
            </span>
            {pageCount > 1 && (
              <div className="pagination" aria-label="Issue table pagination">
                <button
                  aria-label="Previous page"
                  className="icon-button"
                  disabled={safePage === 1}
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                  type="button"
                >
                  <Icon name="chevron-left" />
                </button>
                <span>
                  Page {safePage} of {pageCount}
                </span>
                <button
                  aria-label="Next page"
                  className="icon-button"
                  disabled={safePage === pageCount}
                  onClick={() =>
                    setPage((current) => Math.min(pageCount, current + 1))
                  }
                  type="button"
                >
                  <Icon name="chevron-right" />
                </button>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="table-empty">
          <span>
            <Icon name={issues.length === 0 ? "check" : "search"} />
          </span>
          <strong>
            {issues.length === 0
              ? "No issues were reported"
              : "No issues match these filters"}
          </strong>
          <p>
            {issues.length === 0
              ? "This validation did not return any findings."
              : "Try a different search term or severity."}
          </p>
        </div>
      )}
    </section>
  );
}
