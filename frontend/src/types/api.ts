export type IssueSeverity = "error" | "warning" | "info";

export interface ValidationIssue {
  id: string | number;
  severity: IssueSeverity;
  rule: string;
  row: number | null;
  asset_tag: string | null;
  field: string | null;
  message: string;
  suggestion: string | null;
}

export interface ValidationMetrics {
  total_rows: number;
  valid_rows: number;
  issue_count: number;
  returned_issue_count: number;
  issues_truncated: boolean;
  error_count: number;
  warning_count: number;
  info_count: number;
}

export interface ValidationDownloadUrls {
  excel: string;
  pdf: string;
}

export interface ValidationResult {
  id: string;
  filename: string;
  created_at: string;
  quality_score: number;
  metrics: ValidationMetrics;
  issues: ValidationIssue[];
  download_urls: ValidationDownloadUrls;
}

export interface ValidationSummary {
  id: string;
  filename: string;
  created_at: string;
  quality_score: number;
  metrics: ValidationMetrics;
}

export interface InspectedColumn {
  header: string;
  canonical_field: string | null;
}

export interface InspectionResult {
  filename: string;
  columns: InspectedColumn[];
  unmatched_canonical_fields: string[];
}

export type ColumnMapping = Record<string, string>;

export interface ComparisonAsset {
  asset_tag: string;
  row: number;
}

export interface FieldChange {
  field: string;
  before: string | number | boolean | null;
  after: string | number | boolean | null;
}

export interface ChangedAsset {
  asset_tag: string;
  changes: FieldChange[];
}

export interface ComparisonSummary {
  added: number;
  removed: number;
  changed: number;
  unchanged: number;
}

export interface ComparisonResult {
  id: string;
  before_filename: string;
  after_filename: string;
  created_at: string;
  summary: ComparisonSummary;
  added: ComparisonAsset[];
  removed: ComparisonAsset[];
  changed: ChangedAsset[];
}

export type ReportFormat = "xlsx" | "pdf";
