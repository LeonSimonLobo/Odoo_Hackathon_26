import { cn } from "@/lib/cn";
import { InputHTMLAttributes, forwardRef } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "h-10 w-full rounded-lg border border-border bg-bg-input px-3 text-sm text-text-primary",
          "placeholder:text-text-placeholder",
          "focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary",
          "disabled:cursor-not-allowed disabled:opacity-60",
          "[color-scheme:dark]",
          className,
        )}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";
