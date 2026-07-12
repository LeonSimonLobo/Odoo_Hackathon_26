"use client";

import type { FormEvent, ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import {
  getDashboardKpis,
  getOverdueAllocations,
  getMe,
  login,
  forgotPassword,
  resetPassword,
  type User,
  type Kpis,
  type OverdueAllocation,
} from "@/lib/api";

function inputClassName(extra = "") {
  return [
    "h-11 w-full rounded-2xl border border-stone-200/15 bg-stone-950/45 px-4 text-sm text-stone-100 outline-none placeholder:text-stone-500 focus:border-emerald-300/50",
    extra,
  ]
    .filter(Boolean)
    .join(" ");
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [loginEmail, setLoginEmail] = useState("raj@assetflow.com");
  const [loginPassword, setLoginPassword] = useState("password123");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginSubmitting, setLoginSubmitting] = useState(false);

  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [overdue, setOverdue] = useState<OverdueAllocation[]>([]);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  // Forgot/Reset Password states
  const [loginView, setLoginView] = useState<"signin" | "forgot" | "reset">("signin");
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotSuccess, setForgotSuccess] = useState("");
  const [forgotError, setForgotError] = useState("");
  const [forgotSubmitting, setForgotSubmitting] = useState(false);

  const [resetToken, setResetToken] = useState("");
  const [resetNewPassword, setResetNewPassword] = useState("");
  const [resetConfirmPassword, setResetConfirmPassword] = useState("");
  const [resetSuccess, setResetSuccess] = useState("");
  const [resetError, setResetError] = useState("");
  const [resetSubmitting, setResetSubmitting] = useState(false);

  async function handleForgotPassword(e: FormEvent) {
    e.preventDefault();
    setForgotSubmitting(true);
    setForgotError("");
    setForgotSuccess("");
    try {
      const res = await forgotPassword(forgotEmail);
      setForgotSuccess(res.message || "A reset link was generated! Check the backend console output.");
      setTimeout(() => {
        setLoginView("reset");
      }, 2500);
    } catch (err: unknown) {
      const error = err as Error;
      setForgotError(error.message || "Failed to submit request.");
    } finally {
      setForgotSubmitting(false);
    }
  }

  async function handleResetPassword(e: FormEvent) {
    e.preventDefault();
    if (resetNewPassword !== resetConfirmPassword) {
      setResetError("Passwords do not match");
      return;
    }
    if (resetNewPassword.length < 6) {
      setResetError("Password must be at least 6 characters");
      return;
    }
    setResetSubmitting(true);
    setResetError("");
    setResetSuccess("");
    try {
      await resetPassword(resetToken, resetNewPassword);
      setResetSuccess("Password reset successfully! Redirecting to login...");
      setTimeout(() => {
        setLoginView("signin");
        setResetToken("");
        setResetNewPassword("");
        setResetConfirmPassword("");
        setResetSuccess("");
      }, 2000);
    } catch (err: unknown) {
      const error = err as Error;
      setResetError(error.message || "Failed to reset password.");
    } finally {
      setResetSubmitting(false);
    }
  }



  const loadDashboardData = useCallback(async () => {
    setLoadingDashboard(true);
    setDashboardError(null);
    try {
      const [kpiData, overdueData] = await Promise.all([
        getDashboardKpis(),
        getOverdueAllocations(),
      ]);
      setKpis(kpiData);
      setOverdue(overdueData);
    } catch (error) {
      setDashboardError(error instanceof Error ? error.message : "Failed to load dashboard data");
    } finally {
      setLoadingDashboard(false);
    }
  }, []);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setAuthLoading(false));
  }, []);

  useEffect(() => {
    if (!user) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadDashboardData();
  }, [user, loadDashboardData]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginSubmitting(true);
    setLoginError(null);
    try {
      const result = await login(loginEmail, loginPassword);
      setUser(result.user);
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "Login failed");
    } finally {
      setLoginSubmitting(false);
    }
  }

  if (authLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#111412] text-stone-300">
        Loading AssetFlow...
      </main>
    );
  }

  if (!user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(48,82,62,0.35),_transparent_34%),linear-gradient(180deg,_#0f1110_0%,_#111412_100%)] px-4 py-6 text-stone-100">
        <section className="w-full max-w-md rounded-[2rem] border border-stone-200/15 bg-[#141714] p-8 shadow-[0_28px_90px_rgba(0,0,0,0.45)]">
          <p className="text-sm uppercase tracking-[0.28em] text-emerald-300/80">AssetFlow</p>
          
          {loginView === "signin" && (
            <>
              <h1 className="mt-2 text-3xl font-semibold text-stone-50">Sign in to continue</h1>
              <p className="mt-2 text-sm text-stone-400">
                Asset registry requires authentication. Use a seeded account such as{" "}
                <span className="text-stone-200">Employee: raj@assetflow.com</span> /{" "}
                <span className="text-stone-200">Admin: alice@assetflow.com</span> /{" "}
                <span className="text-stone-200">password123</span>.
              </p>

              <form onSubmit={handleLogin} className="mt-6 space-y-4">
                <Field label="Email" error={loginError ?? undefined}>
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(event) => setLoginEmail(event.target.value)}
                    className={inputClassName()}
                  />
                </Field>
                <Field label="Password">
                  <div className="space-y-1">
                    <input
                      type="password"
                      value={loginPassword}
                      onChange={(event) => setLoginPassword(event.target.value)}
                      className={inputClassName()}
                    />
                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={() => setLoginView("forgot")}
                        className="text-xs font-semibold text-emerald-400 hover:text-emerald-350 transition outline-none mt-1"
                      >
                        Forgot password?
                      </button>
                    </div>
                  </div>
                </Field>
                <button
                  type="submit"
                  disabled={loginSubmitting}
                  className="h-11 w-full rounded-2xl bg-emerald-300 px-4 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-200 disabled:opacity-60"
                >
                  {loginSubmitting ? "Signing in..." : "Sign in"}
                </button>
              </form>
            </>
          )}

          {loginView === "forgot" && (
            <>
              <h1 className="mt-2 text-3xl font-semibold text-stone-50">Recover password</h1>
              <p className="mt-2 text-sm text-stone-400">
                Enter your email address and we will generate a password recovery token in the system logs.
              </p>

              <form onSubmit={handleForgotPassword} className="mt-6 space-y-4">
                <Field label="Email" error={forgotError ?? undefined}>
                  <input
                    type="email"
                    required
                    placeholder="john@assetflow.com"
                    value={forgotEmail}
                    onChange={(event) => setForgotEmail(event.target.value)}
                    className={inputClassName()}
                  />
                </Field>
                
                {forgotSuccess && <p className="text-xs text-emerald-400 font-semibold">{forgotSuccess}</p>}

                <button
                  type="submit"
                  disabled={forgotSubmitting}
                  className="h-11 w-full rounded-2xl bg-emerald-300 px-4 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-200 disabled:opacity-60"
                >
                  {forgotSubmitting ? "Submitting..." : "Send Reset Token"}
                </button>
                
                <div className="flex flex-col gap-2 mt-4 text-center">
                  <button
                    type="button"
                    onClick={() => setLoginView("reset")}
                    className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition outline-none"
                  >
                    Have a reset token? Enter code
                  </button>
                  <button
                    type="button"
                    onClick={() => setLoginView("signin")}
                    className="text-xs font-medium text-stone-400 hover:text-stone-300 transition outline-none"
                  >
                    ← Back to Sign In
                  </button>
                </div>
              </form>
            </>
          )}

          {loginView === "reset" && (
            <>
              <h1 className="mt-2 text-3xl font-semibold text-stone-50">Reset password</h1>
              <p className="mt-2 text-sm text-stone-400">
                Enter your security token and enter a secure new password.
              </p>

              <form onSubmit={handleResetPassword} className="mt-6 space-y-4">
                <Field label="Reset Token" error={resetError ?? undefined}>
                  <input
                    type="text"
                    required
                    placeholder="Enter hex token"
                    value={resetToken}
                    onChange={(event) => setResetToken(event.target.value)}
                    className={inputClassName()}
                  />
                </Field>
                <Field label="New Password">
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={resetNewPassword}
                    onChange={(event) => setResetNewPassword(event.target.value)}
                    className={inputClassName()}
                  />
                </Field>
                <Field label="Confirm Password">
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={resetConfirmPassword}
                    onChange={(event) => setResetConfirmPassword(event.target.value)}
                    className={inputClassName()}
                  />
                </Field>

                {resetSuccess && <p className="text-xs text-emerald-400 font-semibold">{resetSuccess}</p>}

                <button
                  type="submit"
                  disabled={resetSubmitting}
                  className="h-11 w-full rounded-2xl bg-emerald-300 px-4 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-200 disabled:opacity-60"
                >
                  {resetSubmitting ? "Resetting..." : "Reset Password"}
                </button>
                
                <div className="flex justify-center mt-4">
                  <button
                    type="button"
                    onClick={() => setLoginView("signin")}
                    className="text-xs font-medium text-stone-400 hover:text-stone-300 transition outline-none"
                  >
                    ← Back to Sign In
                  </button>
                </div>
              </form>
            </>
          )}
        </section>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen bg-[#0f1110] text-stone-100 selection:bg-emerald-400/30 selection:text-emerald-300">
      <Sidebar currentItem="Dashboard" />

      <section className="flex-1 px-8 py-8 lg:px-12 lg:py-10 flex flex-col overflow-y-auto">
        <header className="border-b border-stone-200/10 pb-5">
            <div>
              <p className="text-sm uppercase tracking-[0.28em] text-emerald-300/80">Screen 2</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-50">
                Dashboard Overview
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-400">
                A real-time snapshot of your company assets, active resource bookings, pending transfer approvals, and overdue returns.
              </p>
              <p className="mt-2 text-xs text-stone-500">
                Signed in as {user.name} ({user.role.replace("_", " ")})
              </p>
            </div>
          </header>

          <div className="flex-1 px-5 py-5 lg:px-7 space-y-6 overflow-y-auto">
            {dashboardError && <div className="text-rose-300 text-sm">{dashboardError}</div>}

            {/* KPI Cards Grid */}
            <div className="grid gap-4 grid-cols-2 lg:grid-cols-3">
              <KpiCard
                label="Assets Available"
                value={kpis ? kpis.assets_available : "—"}
                description="Unallocated and ready for deployment"
                icon="🟢"
              />
              <KpiCard
                label="Assets Allocated"
                value={kpis ? kpis.assets_allocated : "—"}
                description="Currently assigned to employees or depts"
                icon="🏢"
              />
              <KpiCard
                label="Maintenance Today"
                value={kpis ? kpis.maintenance_today : "—"}
                description="Assets undergoing active repairs"
                icon="🔧"
              />
              <KpiCard
                label="Active Bookings"
                value={kpis ? kpis.active_bookings : "—"}
                description="Active rooms, vehicles, or equipment bookings"
                icon="📅"
              />
              <KpiCard
                label="Pending Transfers"
                value={kpis ? kpis.pending_transfers : "—"}
                description="Awaiting manager or head approval"
                icon="🔄"
              />
              <KpiCard
                label="Overdue Returns"
                value={kpis ? kpis.upcoming_returns : "—"}
                description="Overdue return date limits"
                icon="🚨"
                accent={kpis && kpis.upcoming_returns > 0 ? "rose" : "stone"}
              />
            </div>

            {/* Bottom Split Layout */}
            <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
              {/* Overdue Returns Table */}
              <section className="rounded-[1.75rem] border border-stone-200/10 bg-stone-950/20 p-5 flex flex-col">
                <h2 className="text-xl font-semibold text-stone-50">🚨 Overdue Return Logs</h2>
                <p className="text-xs text-stone-400 mt-1 mb-4">
                  These assets are currently overdue past their expected return date. Please coordinate returns.
                </p>

                <div className="overflow-hidden rounded-[1.5rem] border border-stone-200/10 bg-[#171b17] flex-1">
                  <div className="grid grid-cols-[100px_1fr_1.1fr_1.1fr] gap-4 border-b border-stone-200/10 px-5 py-4 text-xs font-semibold uppercase tracking-wider text-stone-300">
                    <span>Tag</span>
                    <span>Name</span>
                    <span>Allocated To</span>
                    <span>Expected Return</span>
                  </div>

                  <div className="divide-y divide-stone-200/10">
                    {loadingDashboard ? (
                      <div className="px-5 py-6 text-sm text-stone-400">Loading records...</div>
                    ) : overdue.length > 0 ? (
                      overdue.map((item) => (
                        <div
                          key={item.id}
                          className="grid grid-cols-[100px_1fr_1.1fr_1.1fr] gap-4 px-5 py-4 text-sm hover:bg-stone-100/5 transition items-center"
                        >
                          <span className="font-semibold text-rose-300">{item.asset_tag}</span>
                          <span className="text-stone-200 truncate">{item.asset_name}</span>
                          <span className="text-stone-300 truncate">{item.target_name}</span>
                          <span className="text-stone-400">
                            {new Date(item.expected_return_date).toLocaleDateString("en-IN")}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="px-5 py-8 text-sm text-stone-500">
                        No overdue assets found. Excellent!
                      </div>
                    )}
                  </div>
                </div>
              </section>

              {/* Quick Actions Panel */}
              <section className="rounded-[1.75rem] border border-stone-200/10 bg-stone-950/20 p-5">
                <h2 className="text-xl font-semibold text-stone-50">⚡ Quick Actions</h2>
                <p className="text-xs text-stone-400 mt-1 mb-4">
                  Perform core resource workflows instantly.
                </p>

                <div className="grid gap-3">
                  <ActionButton
                    title="Register Asset"
                    description="Record a new inventory asset (Admin/Manager)"
                    icon="➕"
                    href="/assets"
                  />
                  <ActionButton
                    title="Raise Maintenance Request"
                    description="Report a damaged or malfunctioning asset"
                    icon="🔧"
                    href="/maintenance"
                  />
                  <ActionButton
                    title="Book Shared Resource"
                    description="Schedule rooms, vehicles, or equipment"
                    icon="📅"
                    href="/bookings"
                  />
                  <ActionButton
                    title="Manage Audit Cycles"
                    description="Run discrepancy checks and verify assets"
                    icon="📝"
                    href="/audit"
                  />
                </div>
              </section>
            </div>
          </div>
        </section>


      </main>
    );
  }

function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <label className="block space-y-2">
      <div className="flex items-center justify-between gap-3 text-sm text-stone-300">
        <span>{label}</span>
        {error ? <span className="text-xs text-rose-300">{error}</span> : null}
      </div>
      {children}
    </label>
  );
}

function KpiCard({
  label,
  value,
  description,
  icon,
  accent = "stone",
}: {
  label: string;
  value: string | number;
  description: string;
  icon: string;
  accent?: "stone" | "rose";
}) {
  return (
    <div className={`rounded-2xl border ${accent === "rose" ? "border-rose-400/35 bg-rose-400/5 shadow-[0_4px_24px_rgba(239,68,68,0.1)]" : "border-stone-200/10 bg-stone-950/35"} px-5 py-4 hover:scale-[1.02] transition duration-200`}>
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.18em] text-stone-500 font-medium">{label}</p>
        <span className="text-lg">{icon}</span>
      </div>
      <p className={`mt-2 text-3xl font-bold tracking-tight ${accent === "rose" ? "text-rose-300" : "text-stone-50"}`}>{value}</p>
      <p className="mt-1 text-[11px] text-stone-400 leading-normal">{description}</p>
    </div>
  );
}

function ActionButton({
  title,
  description,
  icon,
  href,
}: {
  title: string;
  description: string;
  icon: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="flex items-center gap-4 rounded-2xl border border-stone-200/10 bg-stone-950/35 px-4 py-3 hover:bg-emerald-400/5 hover:border-emerald-400/30 transition group duration-200"
    >
      <span className="text-2xl rounded-xl bg-stone-900 p-2.5 group-hover:bg-emerald-400/10 transition">{icon}</span>
      <div className="text-left">
        <p className="text-sm font-semibold text-stone-100 group-hover:text-emerald-300 transition">{title}</p>
        <p className="text-[11px] text-stone-400 leading-normal mt-0.5">{description}</p>
      </div>
    </a>
  );
}
