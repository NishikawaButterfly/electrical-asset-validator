import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type { ComparisonResult, ValidationResult } from "./types/api";

const validationResult: ValidationResult = {
  id: "validation-1",
  filename: "asset-register.csv",
  created_at: "2026-07-30T09:30:00Z",
  quality_score: 82.5,
  metrics: {
    total_rows: 24,
    valid_rows: 22,
    issue_count: 2,
    returned_issue_count: 2,
    issues_truncated: false,
    error_count: 1,
    warning_count: 1,
    info_count: 0,
  },
  issues: [
    {
      id: 101,
      severity: "error",
      rule: "required_asset_tag",
      row: 8,
      asset_tag: null,
      field: "asset_tag",
      message: "Asset tag is missing.",
      suggestion: "Provide a unique asset tag.",
    },
    {
      id: 102,
      severity: "warning",
      rule: "duplicate_circuit",
      row: 14,
      asset_tag: "PDU-A-01",
      field: "circuit",
      message: "Circuit name is duplicated.",
      suggestion: "Confirm the circuit assignment.",
    },
  ],
  download_urls: {
    excel: "/api/v1/validations/validation-1/report.xlsx",
    pdf: "/api/v1/validations/validation-1/report.pdf",
  },
};

const comparisonResult: ComparisonResult = {
  id: "comparison-1",
  before_filename: "revision-a.csv",
  after_filename: "revision-b.xlsx",
  created_at: "2026-07-30T10:00:00Z",
  summary: {
    added: 1,
    removed: 1,
    changed: 1,
    unchanged: 20,
  },
  added: [{ asset_tag: "UPS-B-02", row: 25 }],
  removed: [{ asset_tag: "UPS-B-01", row: 21 }],
  changed: [
    {
      asset_tag: "PDU-A-01",
      changes: [{ field: "panel", before: "LV-01", after: "LV-02" }],
    },
  ],
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(jsonResponse([]))),
    );
  });

  it("starts with honest empty history and no fabricated result", async () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: "Trust the register before it reaches site.",
      }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Quality score")).not.toBeInTheDocument();
    expect(await screen.findByText("No validations yet")).toBeInTheDocument();
  });

  it("uploads a file with the expected multipart field and renders results", async () => {
    const resultWithBoundaryScore = {
      ...validationResult,
      quality_score: 99.9,
    };
    const fetchMock = vi.fn(
      (input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input).endsWith("/api/v1/validations") && init?.method === "POST") {
          return Promise.resolve(jsonResponse(resultWithBoundaryScore));
        }
        return Promise.resolve(jsonResponse([]));
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);

    const file = new File(["asset_tag,circuit\nPDU-A-01,C-01"], "asset-register.csv", {
      type: "text/csv",
    });
    await user.upload(screen.getByLabelText("Asset register"), file);
    await user.click(screen.getByRole("button", { name: "Run validation" }));

    expect(await screen.findByText("Validation complete")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "asset-register.csv" }),
    ).toBeInTheDocument();
    expect(screen.getByText("required_asset_tag")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Quality score: 99.9 out of 100"),
    ).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Quality score: 100 out of 100"),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download Excel" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Download PDF" })).toBeEnabled();

    const postCall = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(postCall).toBeDefined();
    const body = postCall?.[1]?.body as FormData;
    expect(body.get("file")).toBe(file);
  });

  it("compares CSV and XLSX revisions with the expected multipart fields", async () => {
    const fetchMock = vi.fn(
      (input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input).endsWith("/api/v1/comparisons") && init?.method === "POST") {
          return Promise.resolve(jsonResponse(comparisonResult));
        }
        return Promise.resolve(jsonResponse([]));
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("tab", { name: /Compare revisions/ }));
    const before = new File(["asset_tag\nUPS-B-01"], "revision-a.csv", {
      type: "text/csv",
    });
    const after = new File(["workbook"], "revision-b.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    await user.upload(screen.getByLabelText("Before revision"), before);
    await user.upload(screen.getByLabelText("After revision"), after);
    await user.click(screen.getByRole("button", { name: "Compare revisions" }));

    expect(
      await screen.findByRole("heading", { name: "Revision summary" }),
    ).toBeInTheDocument();
    expect(screen.getByText("PDU-A-01")).toBeInTheDocument();
    expect(screen.getByText("LV-01")).toBeInTheDocument();
    expect(screen.getByText("LV-02")).toBeInTheDocument();

    await waitFor(() => {
      const postCall = fetchMock.mock.calls.find(
        ([, init]) => init?.method === "POST",
      );
      const body = postCall?.[1]?.body as FormData;
      expect(body.get("before_file")).toBe(before);
      expect(body.get("after_file")).toBe(after);
    });
  });
});
