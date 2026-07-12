"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Sidebar } from "../Sidebar";
import {
  getActivityLogs,
  getMe,
  getNotifications,
  markNotificationRead,
  type ActivityLog,
  type NotificationItem,
  type User,
} from "@/lib/api";

const POLL_INTERVAL_MS = 30_000;
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

function inputClassName(extra = "") {
  return [
    "h-11 w-full rounded-2xl border border-stone-200/15 bg-stone-950/45 px-4 text-sm text-stone-100 outline-none placeholder:text-stone-500 focus:border-emerald-300/50",
    extra,
  ]
    .filter(Boolean)
    .join(" ");
}

function typeLabel(type: string) {
  return type
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function actionLabel(action: string) {
  return action
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function formatNotificationMessage(notification: NotificationItem) {
  return notification.message;
}

function formatActivityLog(log: ActivityLog) {
  const details = log.details as Record<string, unknown> | null;
  const subject = details?.name ?? details?.asset_name ?? details?.asset_tag ?? details?.title ?? "";
  return subject ? `${subject} · ${actionLabel(log.action)}` : actionLabel(log.action);
}

export default function NotificationsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [socketStatus, setSocketStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");
  const [activeTab, setActiveTab] = useState<"notifications" | "activity">("notifications");
  const [markingId, setMarkingId] = useState<number | null>(null);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [notificationsData, activityData] = await Promise.all([getNotifications(), getActivityLogs()]);
      setNotifications(notificationsData);
      setActivityLogs(activityData);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    getMe().then(setUser).catch(() => setUser(null));
  }, []);

  useEffect(() => {
    if (!user) return;
    const initialLoad = window.setTimeout(() => {
      void loadData();
    }, 0);
    const interval = window.setInterval(() => {
      void loadData();
    }, POLL_INTERVAL_MS);

    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, [loadData, user]);

  useEffect(() => {
    if (!user) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let cancelled = false;

    const connect = () => {
      setSocketStatus("connecting");
      socket = new WebSocket(`${WS_BASE}/ws/notifications`);

      socket.onopen = () => {
        if (cancelled) return;
        setSocketStatus("connected");
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as NotificationItem | { type?: string };
          if ("type" in payload && payload.type === "connected") return;

          const notification = payload as NotificationItem;
          setNotifications((current) => {
            const next = current.filter((item) => item.id !== notification.id);
            return [notification, ...next];
          });
        } catch (error) {
          console.error(error);
        }
      };

      socket.onerror = () => {
        socket?.close();
      };

      socket.onclose = () => {
        if (cancelled) return;
        setSocketStatus("disconnected");
        reconnectTimer = window.setTimeout(connect, 5000);
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [user]);

  const filteredNotifications = useMemo(() => {
    if (filter === "unread") {
      return notifications.filter((notification) => !notification.is_read);
    }
    return notifications;
  }, [filter, notifications]);

  const unreadCount = useMemo(
    () => notifications.filter((notification) => !notification.is_read).length,
    [notifications],
  );

  async function handleMarkRead(id: number) {
    setMarkingId(id);
    try {
      const updated = await markNotificationRead(id);
      setNotifications((current) => current.map((notification) => (notification.id === updated.id ? updated : notification)));
    } catch (error) {
      console.error(error);
    } finally {
      setMarkingId(null);
    }
  }

  if (!user) return null;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(48,82,62,0.35),_transparent_34%),linear-gradient(180deg,_#0f1110_0%,_#111412_100%)] px-4 py-6 text-stone-100 sm:px-6 lg:px-8">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-[1180px] overflow-hidden rounded-[2rem] border border-stone-200/60 bg-[#141714] shadow-[0_28px_90px_rgba(0,0,0,0.45)]">
        <Sidebar currentItem="Notifications" />

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="border-b border-stone-200/10 px-5 py-5 sm:px-6 lg:px-7">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.28em] text-emerald-300/80">Screen 10</p>
                <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-50">Activity logs and notifications</h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-400">
                  Keep every role informed without digging for updates. Notifications refresh every 30 seconds and the audit log shows who did what and when.
                </p>
                <p className="mt-2 text-xs text-stone-500">Signed in as {user.name} ({user.role.replace("_", " ")})</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] xl:w-[560px]">
                <input
                  value={filter}
                  readOnly
                  className={inputClassName("cursor-default capitalize")}
                />
                <div className="flex h-11 items-center justify-center rounded-2xl border border-emerald-300/40 bg-emerald-300/10 px-4 text-sm font-medium text-emerald-100">
                  {unreadCount} unread · {socketStatus}
                </div>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              {[
                { id: "notifications", label: "Notifications" },
                { id: "activity", label: "Activity log" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id as "notifications" | "activity")}
                  className={`rounded-full border px-5 py-1.5 text-sm font-medium transition ${activeTab === tab.id ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-300" : "border-stone-200/20 text-stone-300 hover:border-stone-200/40 hover:bg-stone-200/5"}`}
                >
                  {tab.label}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setFilter(filter === "all" ? "unread" : "all")}
                className="rounded-full border border-stone-200/20 px-5 py-1.5 text-sm font-medium text-stone-300 transition hover:border-stone-200/40 hover:bg-stone-200/5"
              >
                {filter === "all" ? "Show unread only" : "Show all notifications"}
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-auto p-5 lg:p-7">
            {loading ? (
              <p className="text-stone-400">Loading notifications...</p>
            ) : activeTab === "notifications" ? (
              <section className="rounded-[1.75rem] border border-stone-200/10 bg-stone-950/20 p-5">
                <div className="overflow-hidden rounded-[1.5rem] border border-stone-200/10 bg-[#171b17]">
                  <div className="grid grid-cols-[1fr_1.2fr_0.7fr_0.5fr] gap-4 border-b border-stone-200/10 px-5 py-4 text-sm text-stone-300">
                    <span>Type</span>
                    <span>Message</span>
                    <span>Time</span>
                    <span>Status</span>
                  </div>

                  <div className="divide-y divide-stone-200/10">
                    {filteredNotifications.length > 0 ? (
                      filteredNotifications.map((notification) => (
                        <div key={notification.id} className={`grid grid-cols-[1fr_1.2fr_0.7fr_0.5fr] gap-4 px-5 py-4 text-sm ${notification.is_read ? "bg-transparent" : "bg-emerald-300/5"}`}>
                          <div>
                            <p className="font-medium text-stone-100">{typeLabel(notification.type)}</p>
                            <p className="mt-1 text-xs text-stone-500">{notification.title}</p>
                          </div>
                          <p className="text-stone-300">{formatNotificationMessage(notification)}</p>
                          <time className="text-xs text-stone-500">{new Date(notification.created_at).toLocaleString()}</time>
                          <div className="flex items-center justify-between gap-3">
                            <span className={`rounded-full border px-3 py-1 text-xs font-medium ${notification.is_read ? "border-stone-500/40 text-stone-400" : "border-emerald-400/40 text-emerald-300"}`}>
                              {notification.is_read ? "Read" : "New"}
                            </span>
                            {!notification.is_read ? (
                              <button
                                type="button"
                                disabled={markingId === notification.id}
                                onClick={() => void handleMarkRead(notification.id)}
                                className="rounded-full border border-stone-200/15 bg-stone-950/35 px-3 py-1 text-xs font-medium text-stone-200 transition hover:bg-stone-200/10 disabled:opacity-60"
                              >
                                {markingId === notification.id ? "Saving..." : "Mark read"}
                              </button>
                            ) : null}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="px-5 py-8 text-sm text-stone-400">No notifications found.</div>
                    )}
                  </div>
                </div>
              </section>
            ) : (
              <section className="rounded-[1.75rem] border border-stone-200/10 bg-stone-950/20 p-5">
                <div className="overflow-hidden rounded-[1.5rem] border border-stone-200/10 bg-[#171b17]">
                  <div className="grid grid-cols-[1.1fr_1.4fr_0.8fr] gap-4 border-b border-stone-200/10 px-5 py-4 text-sm text-stone-300">
                    <span>Actor</span>
                    <span>Action</span>
                    <span>Time</span>
                  </div>

                  <div className="divide-y divide-stone-200/10">
                    {activityLogs.length > 0 ? (
                      activityLogs.map((log) => (
                        <div key={log.id} className="grid grid-cols-[1.1fr_1.4fr_0.8fr] gap-4 px-5 py-4 text-sm">
                          <div>
                            <p className="font-medium text-stone-100">{log.employee_name}</p>
                            <p className="mt-1 text-xs text-stone-500">{log.employee_id ? `User #${log.employee_id}` : "System action"}</p>
                          </div>
                          <p className="text-stone-300">{formatActivityLog(log)}</p>
                          <time className="text-xs text-stone-500">{new Date(log.created_at).toLocaleString()}</time>
                        </div>
                      ))
                    ) : (
                      <div className="px-5 py-8 text-sm text-stone-400">No activity logs found.</div>
                    )}
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
