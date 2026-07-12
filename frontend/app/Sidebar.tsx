import Link from "next/link";
import { useEffect, useState } from "react";
import { logout, getMe, type User } from "@/lib/api";
import { useNotifications } from "@/lib/NotificationContext";
import {
  LayoutDashboard,
  Building2,
  Package,
  ArrowLeftRight,
  Calendar,
  Wrench,
  ClipboardCheck,
  FileText,
  Bell,
  LogOut,
} from "lucide-react";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Dashboard: LayoutDashboard,
  "Organization setup": Building2,
  Assets: Package,
  "Allocation & Transfer": ArrowLeftRight,
  "Resource Booking": Calendar,
  Maintenance: Wrench,
  Audit: ClipboardCheck,
  Reports: FileText,
  Notifications: Bell,
};

export function Sidebar({ currentItem }: { currentItem: string }) {
  const [user, setUser] = useState<User | null>(null);
  const { unreadCount } = useNotifications();

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  const items = [
    { name: "Dashboard", href: "/" },
    ...(user?.role === "admin"
      ? [{ name: "Organization setup", href: "/organization" }]
      : []),
    { name: "Assets", href: "/assets" },
    { name: "Allocation & Transfer", href: "/allocations" },
    { name: "Resource Booking", href: "/bookings" },
    { name: "Maintenance", href: "/maintenance" },
    { name: "Audit", href: "/audit" },
    { name: "Reports", href: "/reports" },
    { name: "Notifications", href: "/notifications" },
  ];

  async function handleLogout() {
    try {
      await logout();
      window.location.href = "/";
    } catch (error) {
      console.error("Logout failed:", error);
    }
  }

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-bg-surface lg:flex">
      <div className="px-5 py-6">
        <p className="font-heading text-2xl font-bold tracking-tight text-text-primary">
          AssetFlow
        </p>
        <p className="mt-1.5 text-xs leading-relaxed text-text-muted">
          Enterprise asset &amp; resource management
        </p>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {items.map((item) => {
          const isCurrent = item.name === currentItem;
          const showBadge = item.name === "Notifications" && unreadCount > 0;
          const Icon = ICONS[item.name];

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                isCurrent
                  ? "bg-primary/10 text-primary-light"
                  : "text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
              }`}
            >
              <span className="flex items-center gap-3">
                {Icon ? <Icon className="h-4 w-4" /> : null}
                {item.name}
              </span>
              {showBadge ? (
                <span className="flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-warning px-1.5 text-[10px] font-bold text-primary-inverse">
                  {unreadCount}
                </span>
              ) : null}
            </Link>
          );
        })}
      </nav>

      {user && (
        <div className="border-t border-border p-4">
          <div className="mb-3">
            <p className="truncate text-sm font-medium text-text-primary">
              {user.name}
            </p>
            <p className="text-xs capitalize text-text-muted">
              {user.role.replace("_", " ")}
            </p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="flex h-9 w-full items-center justify-center gap-2 rounded-lg border border-border bg-bg-elevated text-xs font-medium text-text-secondary transition hover:border-warning/40 hover:text-warning"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
