import { Sidebar } from "@/app/Sidebar";
import { cn } from "@/lib/cn";

export interface PageShellProps {
  currentItem: string;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function PageShell({
  currentItem,
  title,
  subtitle,
  actions,
  children,
  className,
}: PageShellProps) {
  return (
    <div className="flex min-h-screen bg-bg-app text-text-primary">
      <Sidebar currentItem={currentItem} />
      <main className={cn("flex min-w-0 flex-1 flex-col", className)}>
        <header className="border-b border-border bg-bg-surface/50 px-6 py-5 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h1 className="font-heading text-2xl font-semibold tracking-tight text-text-primary">
                {title}
              </h1>
              {subtitle ? (
                <p className="mt-1 max-w-2xl text-sm leading-relaxed text-text-secondary">
                  {subtitle}
                </p>
              ) : null}
            </div>
            {actions ? (
              <div className="flex shrink-0 flex-wrap items-center gap-3">
                {actions}
              </div>
            ) : null}
          </div>
        </header>
        <div className="flex-1 overflow-auto p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
