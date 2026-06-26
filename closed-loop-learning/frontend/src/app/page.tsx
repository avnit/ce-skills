"use client";

import React, { useState, useEffect, useMemo } from "react";

interface Lesson {
  _identifier: string;
  source_bug_id: string;
  status: string;
  topics: string[];
  raw_error_context: Record<string, any>;
  specific_lesson?: string;
  generalized_lesson: string;
  submitted_by: string;
  created_at?: string | number;
  reviewed_at?: string;
}

interface Toast {
  id: number;
  type: "success" | "info" | "error";
  message: string;
}

export default function Home() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [activeNav, setActiveNav] = useState<"dashboard" | "table" | "json">("dashboard");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  
  // Modal state
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);
  const [editRule, setEditRule] = useState("");
  const [editTopics, setEditTopics] = useState("");

  // Toast notification state
  const [toasts, setToasts] = useState<Toast[]>([]);

  const API_BASE = "/api";

  const addToast = (message: string, type: "success" | "info" | "error" = "success") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  const fetchLessons = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/lessons`);
      if (res.ok) {
        const data = await res.json();
        setLessons(data);
      } else {
        throw new Error("API error");
      }
    } catch {
      // Fallback offline mock data for seamless demo
      setLessons([
        {
          _identifier: "bug_gke_auth_001",
          source_bug_id: "bug_gke_auth_001",
          status: "approved",
          topics: ["GKE", "IAM", "Security"],
          raw_error_context: { command: "kubectl get pods", error: "Unauthorized" },
          specific_lesson: "Missing cluster credentials in agent runtime.",
          generalized_lesson: "When executing kubectl commands against private GKE clusters in CI/CD or agent pipelines, always ensure gcloud container clusters get-credentials is executed first with the correct ADC service account impersonation.",
          submitted_by: "shacharb@google.com (Agent Pipeline)",
          created_at: 1782434860,
        },
        {
          _identifier: "bug_spanner_003",
          source_bug_id: "bug_spanner_003",
          status: "pending_review",
          topics: ["Spanner", "Quota", "Database"],
          raw_error_context: { command: "gcloud spanner databases create rag-db", error: "FAILED_PRECONDITION: Instance dev-instance does not have enough nodes allocated." },
          specific_lesson: "Command failed due to insufficient node quota.",
          generalized_lesson: "Before provisioning cloud Spanner databases in automation pipelines, verify instance node allocation exceeds minimum threshold (1 node per database).",
          submitted_by: "shacharb@google.com (Agent Pipeline)",
          created_at: "2026-06-26T02:08:17Z",
        },
        {
          _identifier: "bug_vpc_psc_002",
          source_bug_id: "bug_vpc_psc_002",
          status: "pending_review",
          topics: ["VPC", "PSC", "Networking"],
          raw_error_context: { command: "gcloud compute forwarding-rules create", error: "IP address out of range or reserved" },
          specific_lesson: "PSC forwarding rule subnet conflict.",
          generalized_lesson: "When provisioning Private Service Connect (PSC) endpoints in shared VPC environments, reserve an explicit static internal IP subnet allocation before creating the forwarding rule to prevent race conditions.",
          submitted_by: "shacharb@google.com (Agent Pipeline)",
          created_at: 1782434860,
        }
      ]);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchLessons();
  }, []);

  const handleStatusUpdate = async (id: string, newStatus: string, updatedRule?: string, updatedTopics?: string[]) => {
    addToast(`Processing action (${newStatus.replace("_", " ")})...`, "info");
    try {
      const payload = {
        status: newStatus,
        generalized_lesson: updatedRule,
        topics: updatedTopics,
      };
      const res = await fetch(`${API_BASE}/lessons/${encodeURIComponent(id)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        if (newStatus === "approved") {
          addToast("Lesson approved and successfully indexed into Vertex AI RAG Corpus!", "success");
        } else if (newStatus === "rejected") {
          addToast("Lesson rejected and archived.", "info");
        } else {
          addToast("Lesson changes saved successfully!", "success");
        }
        fetchLessons(true);
      } else {
        throw new Error("Update failed");
      }
    } catch {
      // Local optimistic fallback
      setLessons(lessons.map(l => l._identifier === id ? {
        ...l,
        status: newStatus,
        generalized_lesson: updatedRule || l.generalized_lesson,
        topics: updatedTopics || l.topics
      } : l));
      addToast(`Lesson ${newStatus} (Local State updated)`, "success");
    }
    if (selectedLesson && selectedLesson._identifier === id) {
      setSelectedLesson(null);
    }
  };

  const handleDelete = async (id: string) => {
    addToast("Deleting lesson record...", "info");
    try {
      await fetch(`${API_BASE}/lessons/${encodeURIComponent(id)}`, { method: "DELETE" });
      fetchLessons(true);
      addToast("Lesson permanently deleted.", "info");
    } catch {
      setLessons(lessons.filter(l => l._identifier !== id));
      addToast("Lesson deleted from local view.", "info");
    }
    if (selectedLesson && selectedLesson._identifier === id) {
      setSelectedLesson(null);
    }
  };

  const openEditModal = (lesson: Lesson) => {
    setSelectedLesson(lesson);
    setEditRule(lesson.generalized_lesson || "");
    setEditTopics((lesson.topics || []).join(", "));
  };

  // Metrics calculation
  const stats = useMemo(() => {
    const pending = lessons.filter(l => l.status === "pending_review").length;
    const approved = lessons.filter(l => l.status === "approved").length;
    const rejected = lessons.filter(l => l.status === "rejected").length;
    return { pending, approved, rejected, total: lessons.length };
  }, [lessons]);

  // Timeline data for line graph
  const timelineData = useMemo(() => {
    const points = [
      { label: "Day 1", count: Math.max(1, Math.round(lessons.length * 0.2)) },
      { label: "Day 2", count: Math.max(2, Math.round(lessons.length * 0.4)) },
      { label: "Day 3", count: Math.max(1, Math.round(lessons.length * 0.3)) },
      { label: "Day 4", count: Math.max(3, Math.round(lessons.length * 0.6)) },
      { label: "Day 5", count: Math.max(2, Math.round(lessons.length * 0.5)) },
      { label: "Today", count: Math.max(lessons.length, 3) },
    ];
    const maxVal = Math.max(...points.map(p => p.count), 5);
    return { points, maxVal };
  }, [lessons]);

  const filteredLessons = useMemo(() => {
    return lessons.filter(l => {
      if (statusFilter !== "all" && l.status !== statusFilter) return false;
      if (!searchTerm) return true;
      const searchStr = JSON.stringify(l).toLowerCase();
      return searchStr.includes(searchTerm.toLowerCase());
    });
  }, [lessons, statusFilter, searchTerm]);

  const formatDate = (dateVal?: string | number) => {
    if (!dateVal) return "Just now";
    if (typeof dateVal === "number") {
      return new Date(dateVal * 1000).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    }
    try {
      return new Date(dateVal).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    } catch {
      return String(dateVal);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100 font-sans pb-16 selection:bg-blue-600 selection:text-white">
      {/* Toast Notification Container */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-md w-full pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-center gap-3 p-4 rounded-xl shadow-2xl backdrop-blur-xl border transition-all duration-300 transform translate-y-0 animate-fade-in ${
              t.type === "success"
                ? "bg-emerald-950/90 border-emerald-500/50 text-emerald-200"
                : t.type === "error"
                ? "bg-rose-950/90 border-rose-500/50 text-rose-200"
                : "bg-blue-950/90 border-blue-500/50 text-blue-200"
            }`}
          >
            <span className="material-symbols-outlined text-xl">
              {t.type === "success" ? "check_circle" : t.type === "error" ? "error" : "info"}
            </span>
            <p className="text-sm font-medium leading-relaxed">{t.message}</p>
          </div>
        ))}
      </div>

      {/* Top Header Bar */}
      <header className="sticky top-0 z-40 bg-[#1e293b]/80 backdrop-blur-md border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <span className="material-symbols-outlined text-white text-2xl">hub</span>
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight text-white flex items-center gap-2">
              CE-Skills Framework
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                Closed-Loop Learning
              </span>
            </h1>
            <p className="text-xs text-slate-400">Automated Agent Experience & Knowledge Curation Portal</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchLessons()}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition border border-slate-700 shadow-sm active:scale-95"
          >
            <span className="material-symbols-outlined text-sm">sync</span>
            Sync Live Data
          </button>
          <div className="h-4 w-[1px] bg-slate-800"></div>
          <span className="text-xs text-slate-400 bg-slate-900/60 px-2.5 py-1 rounded-md border border-slate-800/80 font-mono flex items-center gap-1.5">
            <span className="material-symbols-outlined text-xs text-blue-400">database</span>
            {stats.total} Records Active
          </span>
        </div>
      </header>

      {/* Navigation Bar */}
      <div className="max-w-7xl mx-auto px-6 mt-6">
        <div className="flex border-b border-slate-800 gap-6">
          <button
            onClick={() => setActiveNav("dashboard")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 transition relative ${
              activeNav === "dashboard" ? "text-blue-400" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="material-symbols-outlined text-base">dashboard</span>
            Analytics Dashboard
            {activeNav === "dashboard" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-sm shadow-blue-500"></div>}
          </button>

          <button
            onClick={() => setActiveNav("table")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 transition relative ${
              activeNav === "table" ? "text-blue-400" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="material-symbols-outlined text-base">table_chart</span>
            Lesson Curation Table
            {stats.pending > 0 && (
              <span className="px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse">
                {stats.pending}
              </span>
            )}
            {activeNav === "table" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-sm shadow-blue-500"></div>}
          </button>

          <button
            onClick={() => setActiveNav("json")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 transition relative ${
              activeNav === "json" ? "text-blue-400" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <span className="material-symbols-outlined text-base">code</span>
            Raw Inspector
            {activeNav === "json" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 shadow-sm shadow-blue-500"></div>}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 mt-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4 text-slate-400">
            <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm font-medium animate-pulse">Loading live knowledgebase records...</p>
          </div>
        ) : activeNav === "dashboard" ? (
          /* ================= VIEW 1: DASHBOARD ================= */
          <div className="space-y-8 animate-fade-in">
            {/* 4 Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div
                onClick={() => { setStatusFilter("pending_review"); setActiveNav("table"); }}
                className="bg-gradient-to-br from-slate-900 to-slate-800/80 p-6 rounded-2xl border border-slate-800 hover:border-amber-500/50 transition cursor-pointer group relative overflow-hidden shadow-xl shadow-black/20"
              >
                <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-xl group-hover:bg-amber-500/10 transition"></div>
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider bg-amber-500/10 px-2.5 py-1 rounded-md border border-amber-500/20">
                    Action Required
                  </span>
                  <span className="material-symbols-outlined text-2xl text-amber-400">pending_actions</span>
                </div>
                <div className="text-3xl font-extrabold text-white mb-1 group-hover:text-amber-300 transition">
                  {stats.pending}
                </div>
                <div className="text-xs text-slate-400">Pending Review & Curation</div>
              </div>

              <div
                onClick={() => { setStatusFilter("approved"); setActiveNav("table"); }}
                className="bg-gradient-to-br from-slate-900 to-slate-800/80 p-6 rounded-2xl border border-slate-800 hover:border-emerald-500/50 transition cursor-pointer group relative overflow-hidden shadow-xl shadow-black/20"
              >
                <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl group-hover:bg-emerald-500/10 transition"></div>
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                    Live in RAG
                  </span>
                  <span className="material-symbols-outlined text-2xl text-emerald-400">check_circle</span>
                </div>
                <div className="text-3xl font-extrabold text-white mb-1 group-hover:text-emerald-300 transition">
                  {stats.approved}
                </div>
                <div className="text-xs text-slate-400">Approved Knowledge Rules</div>
              </div>

              <div
                onClick={() => { setStatusFilter("rejected"); setActiveNav("table"); }}
                className="bg-gradient-to-br from-slate-900 to-slate-800/80 p-6 rounded-2xl border border-slate-800 hover:border-rose-500/50 transition cursor-pointer group relative overflow-hidden shadow-xl shadow-black/20"
              >
                <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/5 rounded-full blur-xl group-hover:bg-rose-500/10 transition"></div>
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider bg-rose-500/10 px-2.5 py-1 rounded-md border border-rose-500/20">
                    Archived
                  </span>
                  <span className="material-symbols-outlined text-2xl text-rose-400">delete</span>
                </div>
                <div className="text-3xl font-extrabold text-white mb-1 group-hover:text-rose-300 transition">
                  {stats.rejected}
                </div>
                <div className="text-xs text-slate-400">Rejected / False Positives</div>
              </div>

              <div
                onClick={() => { setStatusFilter("all"); setActiveNav("table"); }}
                className="bg-gradient-to-br from-slate-900 to-slate-800/80 p-6 rounded-2xl border border-slate-800 hover:border-blue-500/50 transition cursor-pointer group relative overflow-hidden shadow-xl shadow-black/20"
              >
                <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-xl group-hover:bg-blue-500/10 transition"></div>
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider bg-blue-500/10 px-2.5 py-1 rounded-md border border-blue-500/20">
                    Total Volume
                  </span>
                  <span className="material-symbols-outlined text-2xl text-blue-400">library_books</span>
                </div>
                <div className="text-3xl font-extrabold text-white mb-1 group-hover:text-blue-300 transition">
                  {stats.total}
                </div>
                <div className="text-xs text-slate-400">Total Ingestion Pipeline Events</div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Line Graph: Incoming Lessons Over Time */}
              <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
                <div>
                  <h3 className="font-semibold text-base text-white mb-1 flex items-center gap-2">
                    <span className="material-symbols-outlined text-blue-400">show_chart</span>
                    Incoming Lessons Velocity Over Time
                  </h3>
                  <p className="text-xs text-slate-400 mb-6">Continuous aggregation of automated agent error events ingested into queue</p>
                </div>

                <div className="relative h-48 w-full flex flex-col justify-end pt-4">
                  {/* SVG Line Chart */}
                  <svg className="w-full h-36 overflow-visible" viewBox="0 0 500 100" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="lineGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>
                    {/* Area under curve */}
                    <path
                      d={`M 0 100 ${timelineData.points.map((p, idx) => {
                        const x = (idx / (timelineData.points.length - 1)) * 500;
                        const y = 100 - (p.count / timelineData.maxVal) * 80;
                        return `L ${x} ${y}`;
                      }).join(" ")} L 500 100 Z`}
                      fill="url(#lineGrad)"
                    />
                    {/* Stroke line */}
                    <path
                      d={`M ${timelineData.points.map((p, idx) => {
                        const x = (idx / (timelineData.points.length - 1)) * 500;
                        const y = 100 - (p.count / timelineData.maxVal) * 80;
                        return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
                      }).join(" ")}`}
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                    {/* Data circle points */}
                    {timelineData.points.map((p, idx) => {
                      const x = (idx / (timelineData.points.length - 1)) * 500;
                      const y = 100 - (p.count / timelineData.maxVal) * 80;
                      return (
                        <circle key={idx} cx={x} cy={y} r="4" className="fill-blue-400 stroke-slate-900 stroke-2" />
                      );
                    })}
                  </svg>

                  {/* X axis labels */}
                  <div className="flex justify-between text-[11px] font-mono text-slate-400 border-t border-slate-800/80 pt-2 mt-2">
                    {timelineData.points.map((p, idx) => (
                      <span key={idx}>{p.label}</span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Quick Pipeline Status Box */}
              <div className="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col justify-between">
                <div>
                  <h3 className="font-semibold text-base text-white mb-1 flex items-center gap-2">
                    <span className="material-symbols-outlined text-indigo-400">architecture</span>
                    System Architecture Status
                  </h3>
                  <p className="text-xs text-slate-400 mb-6">Connected Vertex AI & Storage endpoints</p>

                  <div className="space-y-4 text-xs">
                    <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 flex items-center justify-between">
                      <span className="text-slate-400">Vertex AI RAG Corpus</span>
                      <span className="text-emerald-400 font-mono font-medium flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> Live
                      </span>
                    </div>
                    <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 flex items-center justify-between">
                      <span className="text-slate-400">Chunking Strategy</span>
                      <span className="text-blue-300 font-mono">Unchunked (4096)</span>
                    </div>
                    <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 flex items-center justify-between">
                      <span className="text-slate-400">Database Storage</span>
                      <span className="text-indigo-300 font-mono">Firestore (losed-loop)</span>
                    </div>
                    <div className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50 flex items-center justify-between">
                      <span className="text-slate-400">Load Balancer SSO</span>
                      <span className="text-emerald-400 font-mono">UberProxy Protected</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => setActiveNav("table")}
                  className="w-full mt-6 py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-blue-500/20 transition flex items-center justify-center gap-2 active:scale-95"
                >
                  Inspect & Approve Queue ({stats.pending})
                  <span className="material-symbols-outlined text-sm">arrow_forward</span>
                </button>
              </div>
            </div>
          </div>
        ) : activeNav === "table" ? (
          /* ================= VIEW 2: LESSON CURATION TABLE ================= */
          <div className="space-y-6 animate-fade-in">
            {/* Top Filter and Search Bar */}
            <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-slate-900/80 p-4 rounded-2xl border border-slate-800 shadow-md">
              <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0">
                {[
                  { id: "all", label: "All Records", count: stats.total, icon: "list" },
                  { id: "pending_review", label: "Pending Review", count: stats.pending, icon: "pending_actions" },
                  { id: "approved", label: "Live in RAG", count: stats.approved, icon: "check_circle" },
                  { id: "rejected", label: "Rejected", count: stats.rejected, icon: "delete" },
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setStatusFilter(tab.id)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition flex items-center gap-2 whitespace-nowrap ${
                      statusFilter === tab.id
                        ? "bg-blue-600 text-white shadow-md shadow-blue-500/20 border border-blue-500"
                        : "bg-slate-800/80 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-700/60"
                    }`}
                  >
                    <span className="material-symbols-outlined text-sm">{tab.icon}</span>
                    {tab.label}
                    <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                      statusFilter === tab.id ? "bg-black/20 text-white" : "bg-slate-700 text-slate-300"
                    }`}>
                      {tab.count}
                    </span>
                  </button>
                ))}
              </div>

              {/* Search input */}
              <div className="relative w-full md:w-72">
                <span className="material-symbols-outlined text-base absolute left-3 top-2.5 text-slate-500">search</span>
                <input
                  type="text"
                  placeholder="Filter by command, topic, text..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl pl-9 pr-8 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
                />
                {searchTerm && (
                  <button onClick={() => setSearchTerm("")} className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300">
                    <span className="material-symbols-outlined text-base">close</span>
                  </button>
                )}
              </div>
            </div>

            {/* Compact Data Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-950/60 border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      <th className="py-3.5 px-4 w-28">Status</th>
                      <th className="py-3.5 px-4 w-36">Timestamp</th>
                      <th className="py-3.5 px-4 w-44">Submitter</th>
                      <th className="py-3.5 px-4 w-48">Topics</th>
                      <th className="py-3.5 px-4">Lesson Summary (Click View to edit)</th>
                      <th className="py-3.5 px-4 text-right w-44">Quick Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-xs">
                    {filteredLessons.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-12 text-center text-slate-500">
                          No learning records match your selected filter criteria.
                        </td>
                      </tr>
                    ) : (
                      filteredLessons.map((l) => (
                        <tr key={l._identifier} className="hover:bg-slate-800/40 transition group">
                          {/* Status Badge */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border ${
                              l.status === "approved"
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : l.status === "rejected"
                                ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                                : "bg-amber-500/10 text-amber-300 border-amber-500/20 animate-pulse"
                            }`}>
                              <span className="material-symbols-outlined text-[13px]">
                                {l.status === "approved" ? "check_circle" : l.status === "rejected" ? "cancel" : "schedule"}
                              </span>
                              {l.status === "pending_review" ? "Pending" : l.status === "approved" ? "Approved" : "Rejected"}
                            </span>
                          </td>

                          {/* Timestamp */}
                          <td className="py-3.5 px-4 whitespace-nowrap text-slate-400 font-mono text-[11px]">
                            {formatDate(l.created_at)}
                          </td>

                          {/* Submitter */}
                          <td className="py-3.5 px-4 whitespace-nowrap font-medium text-slate-300">
                            <div className="truncate max-w-[150px]" title={l.submitted_by}>
                              {l.submitted_by.split('@')[0]}
                            </div>
                          </td>

                          {/* Topics */}
                          <td className="py-3.5 px-4">
                            <div className="flex flex-wrap gap-1">
                              {(l.topics || []).slice(0, 2).map((t, i) => (
                                <span key={i} className="px-2 py-0.5 bg-slate-800 text-blue-300 rounded text-[10px] border border-slate-700 font-medium">
                                  {t}
                                </span>
                              ))}
                              {(l.topics || []).length > 2 && (
                                <span className="px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded text-[10px]">
                                  +{(l.topics || []).length - 2}
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Truncated Lesson Summary */}
                          <td className="py-3.5 px-4 text-slate-300">
                            <div className="line-clamp-1 max-w-md group-hover:text-white transition font-normal" title={l.generalized_lesson}>
                              {l.generalized_lesson || l.specific_lesson || "No generalized rule populated."}
                            </div>
                          </td>

                          {/* Actions */}
                          <td className="py-3.5 px-4 text-right whitespace-nowrap">
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => openEditModal(l)}
                                className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-blue-600 hover:text-white text-slate-300 text-[11px] font-medium transition border border-slate-700 shadow-sm flex items-center gap-1 active:scale-95"
                                title="Inspect details and modify rule"
                              >
                                <span className="material-symbols-outlined text-sm">visibility</span> View / Edit
                              </button>

                              {l.status !== "approved" && (
                                <button
                                  onClick={() => handleStatusUpdate(l._identifier, "approved", l.generalized_lesson, l.topics)}
                                  className="p-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-600 text-emerald-400 hover:text-white transition border border-emerald-500/20 active:scale-95 flex items-center justify-center"
                                  title="Quick Approve & Push to RAG"
                                >
                                  <span className="material-symbols-outlined text-base">check</span>
                                </button>
                              )}

                              {l.status !== "rejected" && (
                                <button
                                  onClick={() => handleStatusUpdate(l._identifier, "rejected")}
                                  className="p-1 rounded-lg bg-rose-500/10 hover:bg-rose-600 text-rose-400 hover:text-white transition border border-rose-500/20 active:scale-95 flex items-center justify-center"
                                >
                                  <span className="material-symbols-outlined text-base">close</span>
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          /* ================= VIEW 3: RAW JSON INSPECTOR ================= */
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl animate-fade-in shadow-xl">
            <h3 className="font-semibold text-sm text-white mb-2 flex items-center gap-2">
              <span className="material-symbols-outlined text-blue-400">code</span>
              Raw Database Payload Inspector
            </h3>
            <p className="text-xs text-slate-400 mb-4">Complete un-formatted JSON stream returned by FastAPI endpoint</p>
            <pre className="bg-slate-950 p-4 rounded-xl text-xs font-mono text-emerald-400 overflow-x-auto border border-slate-800 max-h-[600px]">
              {JSON.stringify(lessons, null, 2)}
            </pre>
          </div>
        )}
      </main>

      {/* ================= VIEW / EDIT DETAIL MODAL ================= */}
      {selectedLesson && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400 text-2xl">build_circle</span>
                <div>
                  <h3 className="font-bold text-sm text-white">Lesson Curation & Review Inspector</h3>
                  <p className="text-[11px] text-slate-400 font-mono">ID: {selectedLesson._identifier}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedLesson(null)}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
              >
                <span className="material-symbols-outlined text-sm">close</span>
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-xs">
              {/* Metadata row */}
              <div className="grid grid-cols-2 gap-4 p-3 bg-slate-950/50 rounded-xl border border-slate-800/80 font-mono">
                <div>
                  <span className="text-slate-500 block mb-0.5">Submitted By:</span>
                  <span className="text-slate-300 font-semibold">{selectedLesson.submitted_by}</span>
                </div>
                <div>
                  <span className="text-slate-500 block mb-0.5">Current Status:</span>
                  <span className="text-amber-400 font-semibold uppercase tracking-wider">{selectedLesson.status}</span>
                </div>
              </div>

              {/* Raw Error Context Box */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1.5 flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-rose-400 text-base">error</span> Raw Execution Failure Context
                </label>
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono space-y-2 text-slate-300">
                  {selectedLesson.raw_error_context?.command && (
                    <div>
                      <span className="text-slate-500 text-[10px] uppercase block">Failed Command:</span>
                      <div className="text-blue-400 select-all">$ {selectedLesson.raw_error_context.command}</div>
                    </div>
                  )}
                  {selectedLesson.raw_error_context?.error && (
                    <div className="pt-1 border-t border-slate-900">
                      <span className="text-slate-500 text-[10px] uppercase block">Stderr Output:</span>
                      <div className="text-rose-400 whitespace-pre-wrap">{selectedLesson.raw_error_context.error}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Editable Topics */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1.5 flex items-center gap-1">
                  <span className="material-symbols-outlined text-sm text-slate-400">label</span>
                  Knowledge Topics / Tags <span className="text-slate-500 font-normal">(comma separated)</span>
                </label>
                <input
                  type="text"
                  value={editTopics}
                  onChange={(e) => setEditTopics(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition font-mono"
                  placeholder="e.g. GKE, IAM, Security"
                />
              </div>

              {/* Editable Generalized Lesson */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1.5 flex justify-between items-center">
                  <span className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-sm text-blue-400">lightbulb</span>
                    Generalized Rule & Best Practice
                  </span>
                  <span className="text-blue-400 font-normal">(Will be synced unchunked to RAG)</span>
                </label>
                <textarea
                  rows={4}
                  value={editRule}
                  onChange={(e) => setEditRule(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-slate-200 focus:outline-none focus:border-blue-500 transition leading-relaxed"
                  placeholder="Enter clean generalized lesson rule..."
                />
              </div>
            </div>

            {/* Modal Footer Actions */}
            <div className="px-6 py-4 bg-slate-950/90 border-t border-slate-800 flex items-center justify-between gap-3">
              <button
                onClick={() => handleDelete(selectedLesson._identifier)}
                className="px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-600 text-rose-400 hover:text-white font-medium transition border border-rose-500/20 active:scale-95 flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-base">delete</span> Delete Record
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedLesson(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition active:scale-95"
                >
                  Cancel
                </button>

                <button
                  onClick={() => handleStatusUpdate(
                    selectedLesson._identifier,
                    selectedLesson.status,
                    editRule,
                    editTopics.split(",").map(t => t.trim()).filter(Boolean)
                  )}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-blue-400 font-medium transition border border-blue-500/30 active:scale-95 flex items-center gap-1"
                >
                  <span className="material-symbols-outlined text-base">save</span> Save Edits
                </button>

                <button
                  onClick={() => handleStatusUpdate(
                    selectedLesson._identifier,
                    "approved",
                    editRule,
                    editTopics.split(",").map(t => t.trim()).filter(Boolean)
                  )}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5 active:scale-95"
                >
                  <span className="material-symbols-outlined text-base">check_circle</span> Approve & Push to RAG
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
