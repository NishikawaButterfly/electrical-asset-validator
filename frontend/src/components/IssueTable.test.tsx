import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import type { ValidationIssue } from "../types/api";
import { IssueTable } from "./IssueTable";

const issues: ValidationIssue[] = [
  {
    id: 1,
    severity: "error",
    rule: "required_asset_tag",
    row: 7,
    asset_tag: null,
    field: "asset_tag",
    message: "Asset tag is missing.",
    suggestion: "Provide a unique asset tag.",
  },
  {
    id: 2,
    severity: "warning",
    rule: "duplicate_circuit",
    row: 12,
    asset_tag: "PDU-A-01",
    field: "circuit",
    message: "Circuit name is duplicated.",
    suggestion: "Confirm the circuit assignment.",
  },
];

describe("IssueTable", () => {
  it("filters findings by severity and search text", async () => {
    const user = userEvent.setup();
    render(
      <IssueTable
        issueCount={issues.length}
        issues={issues}
        issuesTruncated={false}
      />,
    );

    expect(screen.getByText("required_asset_tag")).toBeInTheDocument();
    expect(screen.getByText("duplicate_circuit")).toBeInTheDocument();

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Filter by severity" }),
      "warning",
    );
    expect(screen.queryByText("required_asset_tag")).not.toBeInTheDocument();
    expect(screen.getByText("duplicate_circuit")).toBeInTheDocument();

    await user.clear(
      screen.getByRole("searchbox", { name: "Search validation issues" }),
    );
    await user.type(
      screen.getByRole("searchbox", { name: "Search validation issues" }),
      "no match",
    );
    expect(
      screen.getByText("No issues match these filters"),
    ).toBeInTheDocument();
  });

  it("explains when issue details are bounded", () => {
    render(
      <IssueTable
        issueCount={12_500}
        issues={issues}
        issuesTruncated
      />,
    );

    expect(screen.getByText("2 shown")).toBeInTheDocument();
    expect(
      screen.getByText(/bounded set of 12,500 detected issues/i),
    ).toBeInTheDocument();
  });
});
