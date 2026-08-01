import type { ColumnMapping, InspectedColumn } from "../types/api";

interface ColumnMappingPanelProps {
  columns: InspectedColumn[];
  unmatchedFields: string[];
  selections: ColumnMapping;
  disabled?: boolean;
  onSelect: (header: string, field: string) => void;
}

export function ColumnMappingPanel({
  columns,
  unmatchedFields,
  selections,
  disabled = false,
  onSelect,
}: ColumnMappingPanelProps) {
  const unmappedColumns = columns.filter(
    (column) => column.canonical_field === null,
  );
  const selectedFields = new Set(
    Object.values(selections).filter((field) => field !== ""),
  );
  const missingFields = unmatchedFields.filter(
    (field) => !selectedFields.has(field),
  );

  return (
    <section aria-labelledby="mapping-title" className="mapping-panel">
      <strong id="mapping-title">Map unrecognized columns</strong>
      <p aria-live="polite" className="mapping-panel__missing">
        {missingFields.length > 0
          ? `Still missing: ${missingFields.join(", ")}.`
          : "Every canonical field is covered."}
      </p>
      {unmappedColumns.length > 0 && (
        <ul className="mapping-panel__rows">
          {unmappedColumns.map((column, index) => {
            const selectId = `mapping-select-${index}`;
            return (
              <li key={`${column.header}-${index}`} className="mapping-row">
                <label htmlFor={selectId} title={column.header}>
                  {column.header}
                </label>
                <select
                  disabled={disabled}
                  id={selectId}
                  onChange={(event) => onSelect(column.header, event.target.value)}
                  value={selections[column.header] ?? ""}
                >
                  <option value="">Don&apos;t map</option>
                  {unmatchedFields.map((field) => (
                    <option key={field} value={field}>
                      {field}
                    </option>
                  ))}
                </select>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
