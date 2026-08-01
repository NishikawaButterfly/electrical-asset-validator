import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, getErrorMessage } from "./api/client";
import { ColumnMappingPanel } from "./components/ColumnMappingPanel";
import { ComparisonResults } from "./components/ComparisonResults";
import { FileDropzone } from "./components/FileDropzone";
import { Icon } from "./components/Icons";
import { RecentValidations } from "./components/RecentValidations";
import { ValidationResults } from "./components/ValidationResults";
import type {
  ColumnMapping,
  ComparisonResult,
  InspectionResult,
  ReportFormat,
  ValidationResult,
  ValidationSummary,
} from "./types/api";
import { formatQualityScore } from "./utils/format";

type WorkspaceMode = "validate" | "compare";
type SubmissionState = "idle" | "validating" | "comparing";

function toSummary(result: ValidationResult): ValidationSummary {
  return {
    id: result.id,
    filename: result.filename,
    created_at: result.created_at,
    quality_score: result.quality_score,
    metrics: result.metrics,
  };
}

function getDownloadName(filename: string, format: ReportFormat): string {
  const baseName = filename.replace(/\.(csv|xlsx)$/i, "") || "validation";
  return `${baseName}-validation-report.${format}`;
}

export default function App() {
  const [mode, setMode] = useState<WorkspaceMode>("validate");
  const [validationFile, setValidationFile] = useState<File | null>(null);
  const [beforeFile, setBeforeFile] = useState<File | null>(null);
  const [afterFile, setAfterFile] = useState<File | null>(null);
  const [submissionState, setSubmissionState] =
    useState<SubmissionState>("idle");
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [validationResult, setValidationResult] =
    useState<ValidationResult | null>(null);
  const [comparisonResult, setComparisonResult] =
    useState<ComparisonResult | null>(null);
  const [recentItems, setRecentItems] = useState<ValidationSummary[]>([]);
  const [recentLoading, setRecentLoading] = useState(true);
  const [recentError, setRecentError] = useState<string | null>(null);
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<ReportFormat | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [completionAnnouncement, setCompletionAnnouncement] = useState("");
  const [inspection, setInspection] = useState<InspectionResult | null>(null);
  const [mappingSelections, setMappingSelections] = useState<ColumnMapping>({});
  const resultsRef = useRef<HTMLElement>(null);
  const inspectionAbortRef = useRef<AbortController | null>(null);

  const isSubmitting = submissionState !== "idle";
  const unmatchedFields = inspection?.unmatched_canonical_fields ?? [];

  const clearResults = () => {
    setValidationResult(null);
    setComparisonResult(null);
    setCompletionAnnouncement("");
    setDownloadError(null);
  };

  const revealResults = (announcement: string) => {
    setCompletionAnnouncement(announcement);
    window.requestAnimationFrame(() => {
      resultsRef.current?.focus();
      resultsRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  };

  useEffect(() => {
    const controller = new AbortController();

    api
      .listValidations(controller.signal)
      .then((items) => {
        setRecentItems(items);
        setRecentError(null);
      })
      .catch((error: unknown) => {
        if ((error as { name?: string }).name !== "AbortError") {
          setRecentError(getErrorMessage(error));
        }
      })
      .finally(() => setRecentLoading(false));

    return () => controller.abort();
  }, []);

  const selectMode = (nextMode: WorkspaceMode) => {
    if (isSubmitting) return;
    setMode(nextMode);
    setSubmissionError(null);
    if (nextMode !== mode) clearResults();
  };

  const handleValidationFileChange = (file: File | null) => {
    setValidationFile(file);
    setSubmissionError(null);
    clearResults();
    setInspection(null);
    setMappingSelections({});
    inspectionAbortRef.current?.abort();

    if (!file) return;

    const controller = new AbortController();
    inspectionAbortRef.current = controller;

    api
      .createInspection(file, controller.signal)
      .then(setInspection)
      .catch((error: unknown) => {
        // A failed inspection never blocks validation; the backend
        // reports contract problems when the file is submitted.
        if ((error as { name?: string }).name !== "AbortError") {
          setInspection(null);
        }
      });
  };

  const buildMapping = (): ColumnMapping => {
    const mapping: ColumnMapping = {};
    for (const [header, field] of Object.entries(mappingSelections)) {
      if (field !== "") mapping[header] = field;
    }
    return mapping;
  };

  const handleValidation = async (event: FormEvent) => {
    event.preventDefault();
    if (!validationFile || isSubmitting) return;

    setSubmissionState("validating");
    setSubmissionError(null);
    clearResults();

    try {
      const result = await api.createValidation(validationFile, buildMapping());
      setValidationResult(result);
      setComparisonResult(null);
      setRecentItems((items) => [
        toSummary(result),
        ...items.filter((item) => item.id !== result.id),
      ]);
      revealResults(
        `Validation complete for ${result.filename}. Quality score ${formatQualityScore(result.quality_score)} out of 100 with ${result.metrics.issue_count} issues.`,
      );
    } catch (error) {
      setSubmissionError(getErrorMessage(error));
    } finally {
      setSubmissionState("idle");
    }
  };

  const handleComparison = async (event: FormEvent) => {
    event.preventDefault();
    if (!beforeFile || !afterFile || isSubmitting) return;

    setSubmissionState("comparing");
    setSubmissionError(null);
    clearResults();

    try {
      const result = await api.createComparison(beforeFile, afterFile);
      setComparisonResult(result);
      revealResults(
        `Comparison complete. ${result.summary.added} added, ${result.summary.removed} removed, and ${result.summary.changed} changed assets.`,
      );
    } catch (error) {
      setSubmissionError(getErrorMessage(error));
    } finally {
      setSubmissionState("idle");
    }
  };

  const handleOpenValidation = async (id: string) => {
    if (openingId) return;

    setOpeningId(id);
    setSubmissionError(null);
    clearResults();

    try {
      const result = await api.getValidation(id);
      setMode("validate");
      setValidationResult(result);
      revealResults(
        `Opened validation for ${result.filename}. Quality score ${formatQualityScore(result.quality_score)} out of 100 with ${result.metrics.issue_count} issues.`,
      );
    } catch (error) {
      setSubmissionError(getErrorMessage(error));
    } finally {
      setOpeningId(null);
    }
  };

  const handleDownload = async (format: ReportFormat) => {
    if (!validationResult || downloading) return;

    setDownloading(format);
    setDownloadError(null);

    try {
      const report = await api.downloadReport(validationResult.id, format);
      const objectUrl = URL.createObjectURL(report);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = getDownloadName(validationResult.filename, format);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
    } catch (error) {
      setDownloadError(getErrorMessage(error));
    } finally {
      setDownloading(null);
    }
  };

  const demoNotice = String(import.meta.env.VITE_DEMO_NOTICE ?? "").trim();

  return (
    <div className="app-shell">
      {demoNotice ? (
        <p className="demo-notice" role="note">
          {demoNotice}
        </p>
      ) : null}
      <header className="topbar">
        <a className="brand" href="#main">
          <span className="brand__mark">
            <Icon name="spark" />
          </span>
          <span>
            <strong>Electrical Asset Validator</strong>
            <small>Engineering data quality</small>
          </span>
        </a>
        <div className="topbar__context">
          <span className="status-dot" />
          Validation workspace
        </div>
      </header>

      <main id="main">
        <section className="hero">
          <div className="hero__content">
            <p className="eyebrow eyebrow--light">Asset register assurance</p>
            <h1>Trust the register before it reaches site.</h1>
            <p className="hero__lede">
              Check electrical asset data for quality issues, or compare two
              revisions to surface exactly what changed.
            </p>
          </div>
          <div className="hero__checks" aria-label="Validation capabilities">
            <div>
              <Icon name="shield" />
              <span>
                <strong>Deterministic checks</strong>
                <small>Clear, traceable rule findings</small>
              </span>
            </div>
            <div>
              <Icon name="compare" />
              <span>
                <strong>Revision control</strong>
                <small>Added, removed, and changed assets</small>
              </span>
            </div>
          </div>
        </section>

        <div className="content-shell">
          <section className="workspace panel" aria-labelledby="workspace-title">
            <div className="workspace__intro">
              <div>
                <p className="eyebrow">New run</p>
                <h2 id="workspace-title">Start an analysis</h2>
                <p>
                  Upload exported engineering data in CSV or XLSX format.
                </p>
              </div>
              <span className="secure-note">
                <Icon name="shield" />
                Files are sent when you start
              </span>
            </div>

            <div className="mode-tabs" role="tablist" aria-label="Analysis mode">
              <button
                aria-controls="validate-panel"
                aria-selected={mode === "validate"}
                className={mode === "validate" ? "mode-tab mode-tab--active" : "mode-tab"}
                disabled={isSubmitting}
                id="validate-tab"
                onClick={() => selectMode("validate")}
                role="tab"
                type="button"
              >
                <span>
                  <Icon name="shield" />
                </span>
                <span>
                  <strong>Validate file</strong>
                  <small>Run data-quality checks</small>
                </span>
              </button>
              <button
                aria-controls="compare-panel"
                aria-selected={mode === "compare"}
                className={mode === "compare" ? "mode-tab mode-tab--active" : "mode-tab"}
                disabled={isSubmitting}
                id="compare-tab"
                onClick={() => selectMode("compare")}
                role="tab"
                type="button"
              >
                <span>
                  <Icon name="compare" />
                </span>
                <span>
                  <strong>Compare revisions</strong>
                  <small>Find revision differences</small>
                </span>
              </button>
            </div>

            {mode === "validate" ? (
              <form
                aria-labelledby="validate-tab"
                className="analysis-form"
                id="validate-panel"
                onSubmit={handleValidation}
                role="tabpanel"
              >
                <FileDropzone
                  description="Select the asset register you want to check."
                  disabled={isSubmitting}
                  file={validationFile}
                  id="validation-file"
                  label="Asset register"
                  onFileChange={handleValidationFileChange}
                  onInvalidFile={setSubmissionError}
                />
                {validationFile && inspection && unmatchedFields.length > 0 && (
                  <ColumnMappingPanel
                    columns={inspection.columns}
                    disabled={isSubmitting}
                    onSelect={(header, field) =>
                      setMappingSelections((selections) => ({
                        ...selections,
                        [header]: field,
                      }))
                    }
                    selections={mappingSelections}
                    unmatchedFields={unmatchedFields}
                  />
                )}
                <div className="form-action">
                  <span>
                    {validationFile
                      ? "Ready to validate"
                      : "Select one file to continue"}
                  </span>
                  <button
                    className="button button--primary"
                    disabled={!validationFile || isSubmitting}
                    type="submit"
                  >
                    {submissionState === "validating" ? (
                      <>
                        <span className="button-spinner" />
                        Validating…
                      </>
                    ) : (
                      <>
                        Run validation
                        <Icon name="arrow-right" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            ) : (
              <form
                aria-labelledby="compare-tab"
                className="analysis-form"
                id="compare-panel"
                onSubmit={handleComparison}
                role="tabpanel"
              >
                <div className="comparison-files">
                  <FileDropzone
                    description="The earlier asset register."
                    disabled={isSubmitting}
                    file={beforeFile}
                    id="before-file"
                    label="Before revision"
                    onFileChange={(file) => {
                      setBeforeFile(file);
                      setSubmissionError(null);
                      clearResults();
                    }}
                    onInvalidFile={setSubmissionError}
                  />
                  <div className="comparison-arrow" aria-hidden="true">
                    <Icon name="arrow-right" />
                  </div>
                  <FileDropzone
                    description="The updated asset register."
                    disabled={isSubmitting}
                    file={afterFile}
                    id="after-file"
                    label="After revision"
                    onFileChange={(file) => {
                      setAfterFile(file);
                      setSubmissionError(null);
                      clearResults();
                    }}
                    onInvalidFile={setSubmissionError}
                  />
                </div>
                <div className="form-action">
                  <span>
                    {beforeFile && afterFile
                      ? "Ready to compare"
                      : "Select both revisions to continue"}
                  </span>
                  <button
                    className="button button--primary"
                    disabled={!beforeFile || !afterFile || isSubmitting}
                    type="submit"
                  >
                    {submissionState === "comparing" ? (
                      <>
                        <span className="button-spinner" />
                        Comparing…
                      </>
                    ) : (
                      <>
                        Compare revisions
                        <Icon name="arrow-right" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}

            <div aria-live="polite">
              {isSubmitting && (
                <div className="progress-banner" role="status">
                  <span className="progress-banner__icon">
                    <span className="progress-spinner" />
                  </span>
                  <span>
                    <strong>
                      {submissionState === "validating"
                        ? "Validating your asset register"
                        : "Comparing both revisions"}
                    </strong>
                    <small>
                      The service is processing the uploaded{" "}
                      {submissionState === "validating" ? "file" : "files"}.
                    </small>
                  </span>
                  <span className="progress-track">
                    <span />
                  </span>
                </div>
              )}
            </div>

            {submissionError && (
              <div className="inline-alert inline-alert--error" role="alert">
                <Icon name="warning" />
                <span>
                  <strong>Analysis could not be completed</strong>
                  <small>{submissionError}</small>
                </span>
                <button
                  aria-label="Dismiss error"
                  className="icon-button"
                  onClick={() => setSubmissionError(null)}
                  type="button"
                >
                  <Icon name="x" />
                </button>
              </div>
            )}
          </section>

          <aside className="workflow-note">
            <p className="eyebrow">What you receive</p>
            <h2>From raw register to clear action.</h2>
            <ol>
              <li>
                <span>01</span>
                <div>
                  <strong>Upload</strong>
                  <p>Provide an exported CSV or XLSX asset register.</p>
                </div>
              </li>
              <li>
                <span>02</span>
                <div>
                  <strong>Inspect</strong>
                  <p>Review rule, row, asset, and correction guidance.</p>
                </div>
              </li>
              <li>
                <span>03</span>
                <div>
                  <strong>Report</strong>
                  <p>Download the generated Excel or PDF report.</p>
                </div>
              </li>
            </ol>
          </aside>

          {(validationResult || comparisonResult) && (
            <section
              ref={resultsRef}
              aria-label="Analysis results"
              className="results-region"
              id="results"
              tabIndex={-1}
            >
              {validationResult && (
                <ValidationResults
                  downloadError={downloadError}
                  downloading={downloading}
                  onDownload={handleDownload}
                  result={validationResult}
                />
              )}
              {comparisonResult && <ComparisonResults result={comparisonResult} />}
            </section>
          )}

          <p aria-live="polite" className="sr-only">
            {completionAnnouncement}
          </p>

          <RecentValidations
            error={recentError}
            items={recentItems}
            loading={recentLoading}
            onOpen={handleOpenValidation}
            openingId={openingId}
          />
        </div>
      </main>

      <footer>
        <span>Electrical Asset Validator</span>
        <span>Built for traceable engineering data quality.</span>
      </footer>
    </div>
  );
}
