import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: number | string;
  hint?: string;
  icon?: ReactNode;
  tone?: "neutral" | "positive" | "negative" | "warning" | "info";
}

export function MetricCard({
  label,
  value,
  hint,
  icon,
  tone = "neutral",
}: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <div className="metric-card__topline">
        <span>{label}</span>
        {icon}
      </div>
      <strong>{typeof value === "number" ? value.toLocaleString() : value}</strong>
      {hint && <small>{hint}</small>}
    </article>
  );
}
