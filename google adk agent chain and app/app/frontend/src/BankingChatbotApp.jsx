import { useState, useRef, useEffect } from "react";
import {
  Send,
  LogOut,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Users,
  Wallet,
  Building2,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  MapPin,
  Phone,
  ChevronDown,
  Landmark,
  BadgeCheck,
} from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

import ReactMarkdown from "react-markdown";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "https://banking-data-platform-api-699808877074.us-west1.run.app";

const INITIAL_MESSAGES = [
  {
    role: "assistant",
    text: "Hi, I'm the ABC Bank data assistant. Ask me about accounts, transactions, loans, or fraud alerts.",
  },
];

const STATUS_STYLES = {
  Open: { bg: "#FDECEC", text: "#B23A3A" },
  "Under investigation": { bg: "#FDF3E3", text: "#A16A17" },
  Resolved: { bg: "#E7F6EF", text: "#1B7A57" },
};

const FONT_IMPORT = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
  .font-display { font-family: 'Space Grotesk', sans-serif; }
  .font-body { font-family: 'Inter', sans-serif; }
`;

// Fixed, unobtrusive notice that this is a portfolio/demo project and
// not a real bank - shown in the bottom-right corner on every screen.
function DemoDisclaimer() {
  return (
    <div
      className="fixed bottom-3 right-3 z-50 font-body text-[11px] text-slate-400 px-2.5 py-1 rounded-md"
      style={{ background: "rgba(11, 21, 38, 0.55)", backdropFilter: "blur(2px)" }}
    >
      Demo project — not a real financial institution
    </div>
  );
}

// ---------------------------------------------------------------------
// Login screen - styled after institutional net-banking portals:
// utility bar, primary nav, split hero + login panel, trust badges.
// ---------------------------------------------------------------------

function LoginScreen({ onLogin }) {
  const [loginType, setLoginType] = useState("customer"); // "customer" | "employee"
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const idLabel = loginType === "customer" ? "Customer ID" : "Employee ID";
  const idPlaceholder = loginType === "customer" ? "CUSTXXXXXXXX" : "EMPXXXXXXXX";

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!userId.trim() || !password.trim()) {
      setError(`Enter your ${idLabel.toLowerCase()} and password to continue.`);
      return;
    }

    setError("");
    setLoading(true);

    fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_type: loginType.toUpperCase(),
        user_id: userId.trim().toUpperCase(),
        password,
      }),
    })
      .then(async (res) => {
        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.detail || "Invalid credentials");
        }

        onLogin({
          loginType,
          userId: data.user.user_id,
          displayName: data.user.display_name,
          accessToken: data.access_token,
          sessionId: data.session_id,
          user: data.user,
        });
      })
      .catch((err) => {
        setError(err.message || "Unable to sign in.");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div className="min-h-screen w-full flex flex-col" style={{ background: "#F4F6FB" }}>
      <style>{FONT_IMPORT}</style>

      {/* Utility bar */}
      <div
        className="w-full px-4 sm:px-8 py-1.5 flex items-center justify-end gap-4 flex-shrink-0"
        style={{ background: "#081019" }}
      >
        <span className="font-body text-xs text-slate-400 hidden sm:flex items-center gap-1">
          <MapPin size={11} /> Locate a branch
        </span>
        <span className="font-body text-xs text-slate-400 hidden sm:flex items-center gap-1">
          <Phone size={11} /> 1800-XXX-XXXX
        </span>
        <button className="font-body text-xs text-slate-300 flex items-center gap-1 hover:text-white">
          English <ChevronDown size={11} />
        </button>
      </div>

      {/* Primary nav */}
      <header
        className="w-full px-4 sm:px-8 py-3.5 flex items-center justify-between flex-shrink-0"
        style={{ background: "#0B1526", borderBottom: "1px solid #1E2C45" }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: "#2A5CDB" }}
          >
            <Landmark size={18} color="#fff" />
          </div>
          <span className="font-display text-lg font-semibold text-white tracking-tight">
            ABC Bank
          </span>
        </div>

        <nav className="hidden md:flex items-center gap-7">
          {["Personal Banking", "Loans", "Cards", "NRI Banking"].map((item) => (
            <span
              key={item}
              className="font-body text-sm text-slate-300 hover:text-white cursor-pointer"
            >
              {item}
            </span>
          ))}
        </nav>

        <span className="font-body text-sm text-slate-300 hidden sm:block">
          New user? <span style={{ color: "#6FA0F0" }}>Register</span>
        </span>
      </header>

      {/* Hero + login split */}
      <div className="flex-1 relative overflow-hidden">
        {/* Decorative background pattern */}
        <div
          className="absolute inset-0 opacity-[0.04] pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(circle at 2px 2px, #0B1526 1.5px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />
        <div
          className="absolute -top-24 -left-24 w-96 h-96 rounded-full pointer-events-none"
          style={{ background: "radial-gradient(circle, #2A5CDB14 0%, transparent 70%)" }}
        />

        <div className="relative max-w-6xl mx-auto px-6 py-12 lg:py-20 flex flex-col lg:flex-row items-center gap-12">
          {/* Left: messaging */}
          <div className="flex-1 max-w-lg">
            <h1 className="font-display text-3xl sm:text-4xl font-semibold text-slate-900 leading-tight">
              Your accounts, loans, and cards — in one secure view.
            </h1>
            <p className="font-body text-slate-500 mt-4 text-base leading-relaxed">
              Sign in to check balances, track transactions, and get instant
              answers from the ABC Bank data assistant.
            </p>

            <div className="mt-8 space-y-3.5">
              {[
                { icon: ShieldCheck, text: "256-bit encryption on every session" },
                { icon: BadgeCheck, text: "RBI-regulated · deposits insured up to ₹5,00,000" },
                { icon: Lock, text: "Your credentials are never shared with the assistant" },
              ].map((item) => (
                <div key={item.text} className="flex items-center gap-2.5">
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{ background: "#E6EEFC" }}
                  >
                    <item.icon size={14} style={{ color: "#2A5CDB" }} />
                  </div>
                  <span className="font-body text-sm text-slate-600">{item.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: login panel */}
          <div className="w-full max-w-sm flex-shrink-0">
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              {/* Tab switcher */}
              <div className="flex" style={{ background: "#EEF2FA" }}>
                {[
                  { key: "customer", label: "Customer login" },
                  { key: "employee", label: "Employee login" },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => {
                      setLoginType(tab.key);
                      setError("");
                    }}
                    className="font-body flex-1 py-3 text-sm font-medium transition-colors"
                    style={{
                      background: loginType === tab.key ? "#fff" : "transparent",
                      color: loginType === tab.key ? "#0B1526" : "#8B93A7",
                      borderBottom:
                        loginType === tab.key
                          ? "2px solid #2A5CDB"
                          : "2px solid transparent",
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="p-7">
                <h2 className="font-display text-lg font-semibold text-slate-900 mb-0.5">
                  Secure sign in
                </h2>
                <p className="font-body text-xs text-slate-500 mb-5">
                  Enter your {idLabel.toLowerCase()} and password
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="font-body block text-xs font-medium text-slate-600 mb-1.5">
                      {idLabel}
                    </label>
                    <input
                      type="text"
                      value={userId}
                      onChange={(e) => setUserId(e.target.value)}
                      placeholder={idPlaceholder}
                      autoComplete="username"
                      className="font-body w-full px-3.5 py-2.5 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2"
                      style={{ "--tw-ring-color": "#2A5CDB" }}
                    />
                  </div>

                  <div>
                    <label className="font-body block text-xs font-medium text-slate-600 mb-1.5">
                      Password
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter your password"
                        autoComplete="current-password"
                        className="font-body w-full px-3.5 py-2.5 pr-10 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2"
                        style={{ "--tw-ring-color": "#2A5CDB" }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <span
                      className="font-body text-xs cursor-pointer"
                      style={{ color: "#2A5CDB" }}
                    >
                      Forgot {idLabel} or password?
                    </span>
                  </div>

                  {error && (
                    <p className="font-body text-xs" style={{ color: "#D64545" }}>
                      {error}
                    </p>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="font-body w-full py-2.5 rounded-lg text-sm font-medium text-white flex items-center justify-center gap-2 transition-opacity hover:opacity-90"
                    style={{ background: "#2A5CDB" }}
                  >
                    {loading ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <>
                        <Lock size={14} />
                        Secure login
                      </>
                    )}
                  </button>
                </form>
              </div>

              <div
                className="px-7 py-3.5 flex items-center justify-center gap-4"
                style={{ background: "#F8FAFD", borderTop: "1px solid #EEF1F6" }}
              >
                <span className="font-body text-[11px] text-slate-400 flex items-center gap-1">
                  <ShieldCheck size={12} /> SSL secured
                </span>
                <span className="font-body text-[11px] text-slate-400 flex items-center gap-1">
                  <BadgeCheck size={12} /> RBI regulated
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer
        className="w-full px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 flex-shrink-0"
        style={{ background: "#0B1526" }}
      >
        <span className="font-body text-xs text-slate-500">
          © 2026 ABC Bank. All rights reserved.
        </span>
        <div className="flex items-center gap-5">
          {["Privacy", "Security", "Terms"].map((item) => (
            <span key={item} className="font-body text-xs text-slate-500 hover:text-slate-300 cursor-pointer">
              {item}
            </span>
          ))}
        </div>
      </footer>

      <DemoDisclaimer />
    </div>
  );
}

// ---------------------------------------------------------------------
// Dynamic dashboard renderer
// ---------------------------------------------------------------------

function AssistantMessage({ text }) {
  const safeText = String(text || "").trim();

  // Turn responses made of labelled details such as
  // **Full Name:** Isaac - **Customer ID:** CUST... into a clean detail card.
  const detailMatches = [
    ...safeText.matchAll(/\*\*([^*]+?)\:\*\*\s*([^\n]+?)(?=\s+-\s+\*\*|$)/g),
  ];

  const isDetailResponse =
    detailMatches.length >= 2 &&
    detailMatches.length >= (safeText.match(/\*\*[^*]+?\:\*\*/g) || []).length * 0.7;

  if (isDetailResponse) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg flex items-center justify-center bg-blue-50 border border-blue-100">
            <BadgeCheck size={15} style={{ color: "#2A5CDB" }} />
          </div>
          <div>
            <p className="font-display text-sm font-semibold text-slate-900">
              Customer details
            </p>
            <p className="font-body text-[11px] text-slate-400">
              Information associated with your account
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {detailMatches.map((match, index) => {
            const label = match[1].trim();
            const value = match[2].trim().replace(/\s+-\s*$/, "");
            return (
              <div
                key={`${label}-${index}`}
                className="rounded-xl border border-slate-200 bg-white px-3.5 py-3 shadow-sm"
              >
                <p className="font-body text-[10px] uppercase tracking-[0.08em] font-semibold text-slate-400">
                  {label}
                </p>
                <p className="font-body text-sm font-medium text-slate-800 mt-1 break-words">
                  {value}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="assistant-markdown font-body text-sm leading-6 text-slate-700">
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <p className="mb-2 last:mb-0">{children}</p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-slate-900">{children}</strong>
          ),
          ul: ({ children }) => (
            <ul className="my-2 ml-4 list-disc space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-2 ml-4 list-decimal space-y-1">{children}</ol>
          ),
          li: ({ children }) => <li className="pl-1">{children}</li>,
          h1: ({ children }) => (
            <h1 className="font-display text-base font-semibold text-slate-900 mb-2">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="font-display text-sm font-semibold text-slate-900 mb-2">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="font-display text-sm font-semibold text-slate-900 mb-1.5">{children}</h3>
          ),
          blockquote: ({ children }) => (
            <div className="border-l-2 border-blue-200 pl-3 my-2 text-slate-500">{children}</div>
          ),
          code: ({ inline, children }) =>
            inline ? (
              <code className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[12px] text-slate-700">{children}</code>
            ) : (
              <pre className="my-2 overflow-x-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
                <code>{children}</code>
              </pre>
            ),
        }}
      >
        {safeText}
      </ReactMarkdown>
    </div>
  );
}

function DashboardRenderer({ dashboard }) {
  if (!dashboard || !dashboard.columns || !dashboard.rows) {
    return null;
  }

  const data = dashboard.rows.map((row) => {
    const item = {};

    dashboard.columns.forEach((column, index) => {
      item[column] = row[index];
    });

    return item;
  });

  const getChartType = (chart) =>
    String(chart.chart_type || "").trim().toLowerCase();

  const getNumericValue = (chart) => {
    const column = chart.y_columns?.[0];

    if (!column || !data.length) {
      return "0";
    }

    const value = data[0][column];
    const number = Number(value);

    if (Number.isFinite(number)) {
      return number.toLocaleString("en-IN", {
        maximumFractionDigits: 2,
      });
    }

    return String(value ?? "0");
  };

  const getKpiIcon = (title = "") => {
    const normalizedTitle = title.toLowerCase();

    if (
      normalizedTitle.includes("customer") ||
      normalizedTitle.includes("client")
    ) {
      return Users;
    }

    if (
      normalizedTitle.includes("account") ||
      normalizedTitle.includes("balance")
    ) {
      return Wallet;
    }

    if (
      normalizedTitle.includes("fraud") ||
      normalizedTitle.includes("alert")
    ) {
      return AlertTriangle;
    }

    if (
      normalizedTitle.includes("branch") ||
      normalizedTitle.includes("employee")
    ) {
      return Building2;
    }

    if (
      normalizedTitle.includes("transaction") ||
      normalizedTitle.includes("volume")
    ) {
      return TrendingUp;
    }

    return Landmark;
  };

  const getKpiAccent = (index) => {
    const accents = [
      "#2A5CDB",
      "#1F9D77",
      "#D64545",
      "#C98A1E",
    ];

    return accents[index % accents.length];
  };

  const renderChart = (chart, index) => {
    const chartType = getChartType(chart);
    const xColumn = chart.x_column;
    const yColumns = chart.y_columns || [];

    if (chartType === "kpi") {
      const Icon = getKpiIcon(chart.title);
      const accent = getKpiAccent(index);

      return (
        <div
          key={index}
          className="bg-white rounded-xl p-4 border border-slate-100"
          style={{ borderLeft: `3px solid ${accent}` }}
        >
          <div className="flex items-center justify-between">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: `${accent}14` }}
            >
              <Icon size={16} style={{ color: accent }} />
            </div>
          </div>

          <p className="font-body text-xs text-slate-500 mt-3">
            {chart.title}
          </p>

          <p className="font-display text-2xl font-semibold text-slate-900 mt-1">
            {getNumericValue(chart)}
          </p>
        </div>
      );
    }

    if (chartType === "table") {
      return (
        <div
          key={index}
          className="bg-white rounded-xl p-4 border border-slate-100"
        >
          <h3 className="font-display text-sm font-semibold text-slate-800 mb-3">
            {chart.title}
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50">
                  {dashboard.columns.map((column) => (
                    <th
                      key={column}
                      className="text-left px-3 py-2 font-medium text-slate-600"
                    >
                      {column}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {dashboard.rows.slice(0, 100).map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className="border-t border-slate-100"
                  >
                    {row.map((cell, cellIndex) => (
                      <td
                        key={cellIndex}
                        className="px-3 py-2 text-slate-700"
                      >
                        {String(cell ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    const common = (
      <>
        <CartesianGrid
          strokeDasharray="3 3"
          vertical={false}
          stroke="#EEF1F6"
        />
        <XAxis dataKey={xColumn} tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
      </>
    );

    if (chartType === "pie") {
      const valueColumn = yColumns[0];

      return (
        <div
          key={index}
          className="bg-white rounded-xl p-4 border border-slate-100"
        >
          <h3 className="font-display text-sm font-semibold text-slate-800 mb-3">
            {chart.title}
          </h3>

          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={data}
                  dataKey={valueColumn}
                  nameKey={xColumn}
                  cx="50%"
                  cy="50%"
                  outerRadius={95}
                  label
                >
                  {data.map((_, i) => (
                    <Cell
                      key={i}
                      fill={
                        [
                          "#2A5CDB",
                          "#1F9D77",
                          "#C98A1E",
                          "#D64545",
                        ][i % 4]
                      }
                    />
                  ))}
                </Pie>

                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }

    const ChartComponent =
      chartType === "line"
        ? LineChart
        : chartType === "area"
          ? AreaChart
          : BarChart;

    return (
      <div
        key={index}
        className="bg-white rounded-xl p-4 border border-slate-100"
      >
        <h3 className="font-display text-sm font-semibold text-slate-800 mb-3">
          {chart.title}
        </h3>

        <div style={{ width: "100%", height: 300 }}>
          <ResponsiveContainer>
            <ChartComponent data={data}>
              {common}

              {yColumns.map((column, i) =>
                chartType === "line" ? (
                  <Line
                    key={column}
                    type="monotone"
                    dataKey={column}
                    stroke={
                      [
                        "#2A5CDB",
                        "#1F9D77",
                        "#C98A1E",
                      ][i % 3]
                    }
                    strokeWidth={2}
                    dot={false}
                  />
                ) : chartType === "area" ? (
                  <Area
                    key={column}
                    type="monotone"
                    dataKey={column}
                    stroke={
                      [
                        "#2A5CDB",
                        "#1F9D77",
                        "#C98A1E",
                      ][i % 3]
                    }
                    fill={
                      [
                        "#2A5CDB",
                        "#1F9D77",
                        "#C98A1E",
                      ][i % 3]
                    }
                    fillOpacity={0.15}
                  />
                ) : (
                  <Bar
                    key={column}
                    dataKey={column}
                    fill={
                      [
                        "#2A5CDB",
                        "#1F9D77",
                        "#C98A1E",
                      ][i % 3]
                    }
                    radius={[4, 4, 0, 0]}
                  />
                )
              )}
            </ChartComponent>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  return (
    <div className="mt-4 space-y-3 w-full">
      {dashboard.title && (
        <div>
          <h2 className="font-display text-lg font-semibold text-slate-900">
            {dashboard.title}
          </h2>

          {dashboard.description && (
            <p className="font-body text-xs text-slate-500 mt-1">
              {dashboard.description}
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {dashboard.charts?.map(renderChart)}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------
// Dashboard (chat + analytics)
// ---------------------------------------------------------------------

function Dashboard({ session, onLogout }) {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState("");
  const scrollRef = useRef(null);

  const isEmployee = session.loginType === "employee";

  const displayLabel =
    session.user?.role ||
    (isEmployee ? "Employee" : "Customer");

  const initials = (
    session.displayName || session.userId
  )
    .slice(0, 2)
    .toUpperCase();

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isThinking]);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setDashboardLoading(true);
        setDashboardError("");

        const res = await fetch(`${API_URL}/dashboard/summary`, {
          method: "GET",
          headers: {
            "X-Access-Token": session.accessToken,
          },
        });

        const data = await res.json();

        if (res.status === 401) {
          onLogout();
          return;
        }

        if (!res.ok) {
          throw new Error(
            data.detail || "Unable to load dashboard data."
          );
        }

        setDashboardData(data);
      } catch (err) {
        setDashboardError(
          err.message || "Unable to load dashboard data."
        );
      } finally {
        setDashboardLoading(false);
      }
    };

    loadDashboard();
  }, [session.accessToken, onLogout]);

  const handleSend = async () => {
    const text = input.trim();

    if (!text || isThinking) {
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        text,
      },
    ]);

    setInput("");
    setIsThinking(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Access-Token": session.accessToken,
        },
        body: JSON.stringify({
          session_id: session.sessionId,
          message: text,
        }),
      });

      const data = await res.json();

      if (res.status === 401) {
        onLogout();
        return;
      }

      if (!res.ok) {
        throw new Error(
          data.detail || "Unable to process your request."
        );
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            data.response ||
            "I was unable to generate a response.",
          dashboard: data.dashboard || null,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            err.message ||
            "Unable to connect to the banking assistant.",
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className="min-h-screen w-full flex flex-col"
      style={{ background: "#F4F6FB" }}
    >
      <style>{FONT_IMPORT}</style>

      {/* Top bar */}
      <header
        className="flex items-center justify-between px-6 py-3.5 flex-shrink-0"
        style={{ background: "#0B1526" }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "#2A5CDB" }}
          >
            <Landmark size={16} color="#fff" />
          </div>

          <span className="font-display text-base font-semibold text-white tracking-tight">
            ABC Bank
          </span>

          <span className="font-body text-xs text-slate-400 ml-1 hidden sm:inline">
            Data Assistant
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="font-body text-sm text-white leading-tight">
              {session.displayName || session.userId}
            </p>

            <p className="font-body text-xs text-slate-400 leading-tight">
              {displayLabel}
            </p>
          </div>

          <div
            className="w-8 h-8 rounded-full flex items-center justify-center font-body text-xs font-medium text-white flex-shrink-0"
            style={{ background: "#2A5CDB" }}
          >
            {initials}
          </div>

          <button
            onClick={onLogout}
            className="text-slate-400 hover:text-white transition-colors p-1.5"
            aria-label="Log out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 lg:p-6 max-w-7xl w-full mx-auto min-h-0">
        {/* Chat panel - hero */}
        <div className="flex-1 flex flex-col bg-white rounded-2xl shadow-lg min-h-[520px] lg:min-h-0">
          <div className="px-5 py-4 border-b border-slate-100">
            <h1 className="font-display text-base font-semibold text-slate-900">
              Ask about your data
            </h1>

            <p className="font-body text-xs text-slate-500 mt-0.5">
              Accounts, transactions, loans, and fraud alerts
            </p>
          </div>

          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto px-5 py-4 space-y-4"
          >
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${
                  msg.role === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl px-4 py-3 font-body text-sm shadow-sm ${
                    msg.role === "user"
                      ? "text-white rounded-br-sm"
                      : "text-slate-800 rounded-bl-sm"
                  }`}
                  style={{
                    background:
                      msg.role === "user"
                        ? "#2A5CDB"
                        : "#FFFFFF",
                  }}
                >
                  {msg.role === "assistant" ? (
                    <AssistantMessage text={msg.text} />
                  ) : (
                    <p>{msg.text}</p>
                  )}

                  {msg.dashboard && (
                    <DashboardRenderer
                      dashboard={msg.dashboard}
                    />
                  )}

                  {msg.table && (
                    <div className="mt-3 rounded-lg overflow-hidden border border-slate-200 bg-white">
                      <table className="w-full text-xs">
                        <thead>
                          <tr style={{ background: "#EEF2FA" }}>
                            {msg.table.columns.map((col) => (
                              <th
                                key={col}
                                className="font-body text-left font-medium text-slate-600 px-3 py-2"
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>

                        <tbody>
                          {msg.table.rows.map((row, rIdx) => (
                            <tr
                              key={rIdx}
                              className="border-t border-slate-100"
                            >
                              {row.map((cell, cIdx) => (
                                <td
                                  key={cIdx}
                                  className="font-body px-3 py-2 text-slate-700"
                                >
                                  {cell}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isThinking && (
              <div className="flex justify-start">
                <div
                  className="rounded-xl rounded-bl-sm px-4 py-2.5 flex items-center gap-1.5"
                  style={{ background: "#F1F4FA" }}
                >
                  <Loader2
                    size={14}
                    className="animate-spin text-slate-400"
                  />

                  <span className="font-body text-xs text-slate-400">
                    Thinking
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="px-4 py-3 border-t border-slate-100">
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g. How many fraud alerts are open this week?"
                rows={1}
                className="font-body flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2"
                style={{ "--tw-ring-color": "#2A5CDB" }}
              />

              <button
                onClick={handleSend}
                className="p-2.5 rounded-lg text-white flex-shrink-0 transition-opacity hover:opacity-90"
                style={{ background: "#2A5CDB" }}
                aria-label="Send message"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Analytics rail */}
        <div className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-4">
          {/* KPI cards */}
          <div className="grid grid-cols-2 gap-3">
            <div
              className="bg-white rounded-xl p-3.5"
              style={{ borderLeft: "3px solid #2A5CDB" }}
            >
              <Users
                size={16}
                style={{ color: "#2A5CDB" }}
              />

              <p className="font-display text-lg font-semibold text-slate-900 mt-2 leading-none">
                {dashboardLoading
                  ? "..."
                  : dashboardData?.kpis?.active_customers?.toLocaleString?.(
                      "en-IN"
                    ) ?? "—"}
              </p>

              <p className="font-body text-xs text-slate-500 mt-1">
                Active customers
              </p>
            </div>

            <div
              className="bg-white rounded-xl p-3.5"
              style={{ borderLeft: "3px solid #1F9D77" }}
            >
              <Wallet
                size={16}
                style={{ color: "#1F9D77" }}
              />

              <p className="font-display text-lg font-semibold text-slate-900 mt-2 leading-none">
                {dashboardLoading
                  ? "..."
                  : dashboardData?.kpis?.open_accounts?.toLocaleString?.(
                      "en-IN"
                    ) ?? "—"}
              </p>

              <p className="font-body text-xs text-slate-500 mt-1">
                Open accounts
              </p>
            </div>

            {isEmployee && (
              <div
                className="bg-white rounded-xl p-3.5"
                style={{ borderLeft: "3px solid #C98A1E" }}
              >
                <TrendingUp
                  size={16}
                  style={{ color: "#C98A1E" }}
                />

                <p className="font-display text-lg font-semibold text-slate-900 mt-2 leading-none">
                  {dashboardLoading
                    ? "..."
                    : dashboardData?.kpis?.total_transactions?.toLocaleString?.(
                        "en-IN"
                      ) ?? "—"}
                </p>

                <p className="font-body text-xs text-slate-500 mt-1">
                  Total transactions
                </p>
              </div>
            )}

            <div
              className="bg-white rounded-xl p-3.5"
              style={{ borderLeft: "3px solid #C98A1E" }}
            >
              <Building2
                size={16}
                style={{ color: "#C98A1E" }}
              />

              <p className="font-display text-lg font-semibold text-slate-900 mt-2 leading-none">
                {dashboardLoading
                  ? "..."
                  : dashboardData?.kpis?.branches?.toLocaleString?.(
                      "en-IN"
                    ) ?? "—"}
              </p>

              <p className="font-body text-xs text-slate-500 mt-1">
                Branches
              </p>
            </div>
          </div>

          {dashboardError && (
            <div className="bg-white rounded-xl p-4">
              <p className="font-body text-xs text-slate-500">
                {dashboardError}
              </p>
            </div>
          )}

          {/* Quarterly transactions - employees only */}
          {isEmployee && (
            <div className="bg-white rounded-xl p-4">
              <div className="flex items-center gap-1.5 mb-3">
                <TrendingUp
                  size={14}
                  style={{ color: "#2A5CDB" }}
                />

                <h2 className="font-body text-sm font-medium text-slate-700">
                  Transactions this Quarter
                </h2>
              </div>

              <div style={{ width: "100%", height: 140 }}>
                <ResponsiveContainer>
                  <BarChart
                    data={
                      dashboardData?.quarter_transactions ?? []
                    }
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#EEF1F6"
                    />

                    <XAxis
                      dataKey="day"
                      tick={{
                        fontSize: 11,
                        fill: "#94A3B8",
                      }}
                      axisLine={false}
                      tickLine={false}
                    />

                    <YAxis hide />

                    <Tooltip
                      cursor={{ fill: "#F4F6FB" }}
                      contentStyle={{
                        fontSize: 12,
                        borderRadius: 8,
                        border: "1px solid #E2E8F0",
                      }}
                    />

                    <Bar
                      dataKey="volume"
                      fill="#2A5CDB"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recent fraud alerts - customers only */}
          {!isEmployee && (
            <div className="bg-white rounded-xl p-4">
              <div className="flex items-center gap-1.5 mb-3">
                <AlertTriangle
                  size={14}
                  style={{ color: "#D64545" }}
                />

                <h2 className="font-body text-sm font-medium text-slate-700">
                  Recent fraud alerts
                </h2>
              </div>

              <div className="space-y-2.5">
                {dashboardLoading ? (
                  <p className="font-body text-xs text-slate-400">
                    Loading alerts...
                  </p>
                ) : dashboardData?.recent_alerts?.length ? (
                  dashboardData.recent_alerts.map((alert) => {
                    const statusStyle =
                      STATUS_STYLES[alert.alert_status] || {
                        bg: "#F1F4FA",
                        text: "#64748B",
                      };

                    return (
                      <div
                        key={alert.alert_id}
                        className="flex items-center justify-between gap-2"
                      >
                        <div className="min-w-0">
                          <p className="font-body text-xs font-medium text-slate-800 truncate">
                            {alert.alert_reason}
                          </p>

                          <p className="font-body text-xs text-slate-400">
                            {alert.alert_id}
                          </p>
                        </div>

                        <span
                          className="font-body text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0"
                          style={{
                            background: statusStyle.bg,
                            color: statusStyle.text,
                          }}
                        >
                          {alert.alert_status}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <p className="font-body text-xs text-slate-400">
                    No fraud alerts found.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <DemoDisclaimer />
    </div>
  );
}

// ---------------------------------------------------------------------
// App root
// ---------------------------------------------------------------------

export default function App() {
  const [session, setSession] = useState(null);

  if (!session) {
    return <LoginScreen onLogin={setSession} />;
  }

  return (
    <Dashboard
      session={session}
      onLogout={() => {
        setSession(null);
      }}
    />
  );
}
