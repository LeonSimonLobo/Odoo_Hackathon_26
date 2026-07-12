import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import { LucideIcon } from "lucide-react";

export function KpiCard({
  label,
  value,
  description,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  accent?: "warning" | "success" | "primary";
}) {
  const accentClasses = {
    warning: "text-warning",
    success: "text-success",
    primary: "text-primary-light",
  };

  return (
    <Card className="flex flex-col justify-between">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-wide text-text-muted">
          {label}
        </p>
        {Icon ? (
          <Icon
            className={cn(
              "h-5 w-5 shrink-0 text-text-muted",
              accent && accentClasses[accent],
            )}
          />
        ) : null}
      </div>
      <div className="mt-3">
        <p
          className={cn(
            "text-3xl font-semibold tracking-tight text-text-primary",
            accent && accentClasses[accent],
          )}
        >
          {value}
        </p>
        {description ? (
          <p className="mt-1 text-xs leading-relaxed text-text-secondary">
            {description}
          </p>
        ) : null}
      </div>
    </Card>
  );
}
