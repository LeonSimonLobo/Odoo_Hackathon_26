import { cn } from "@/lib/cn";

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: "default" | "primary" | "warning" | "success" | "muted";
  className?: string;
}) {
  const variants = {
    default:
      "border-border bg-bg-elevated text-text-secondary",
    primary:
      "border-primary/30 bg-primary/10 text-primary-light",
    warning:
      "border-warning/30 bg-warning/10 text-warning-light",
    success:
      "border-success/30 bg-success/10 text-success",
    muted:
      "border-border-subtle bg-bg-input text-text-muted",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
