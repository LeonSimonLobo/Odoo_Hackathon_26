import { cn } from "@/lib/cn";
import { LabelHTMLAttributes } from "react";

export function Label({
  children,
  className,
  ...props
}: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("mb-1.5 block text-sm font-medium text-text-secondary", className)}
      {...props}
    >
      {children}
    </label>
  );
}
