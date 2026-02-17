import "./App.css";
import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

type MeContext = {
  profile: { user_id: number; email: string | null; roles: string[] };
  global_permissions: {
    can_access_platform: boolean;
    can_create_projects: boolean;
    can_manage_agent_catalog: boolean;
    can_issue_dev_tokens: boolean;
    can_manage_security: boolean;
  };
  projects: Array<{
    project_id: number;
    project_key: string;
    project_name: string;
    lifecycle_status: string;
    member_role: string;
    updated_at: string;
  }>;
};

type MeDashboard = {
  user_id: number;
  generated_at: string;
  kpis: {
    projects_count: number;
    blocked_stages_count: number;
    failed_runs_count_7d: number;
    queued_runs_count: number;
    published_artifacts_count: number;
    cost_usd_total_30d: number;
  };
  projects?: Array<{
    project_id: number;
    project_key: string;
    project_name: string;
    lifecycle_status: string;
    member_role: string;
    blocked_stages_count: number;
    failed_runs_count_7d: number;
    queued_runs_count: number;
    cost_usd_total_30d: number;
    updated_at: string;
  }>;
};

type CostSummary = {
  total_cost_usd: number;
  total_runs_count: number;
  by_provider: Array<{ provider: string; total_cost_usd: number; runs_count: number }>;
  by_model?: Array<{ provider: string | null; model_name: string | null; total_cost_usd: number; runs_count: number }>;
};

type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
};

type TabName = "overview" | "projects" | "costs" | "ideas" | "agents";
type SourceName = "context" | "dashboard" | "costs";
type SourceStatus = Record<SourceName, "idle" | "ok" | "error">;

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const SESSION_TOKEN_KEY = "plataforma_ia_access_token";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatDate(input?: string): string {
  if (!input) return "-";
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) return "-";
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(d);
}

function humanError(label: string, status: number): string {
  if (status >= 500) return `${label}: backend no disponible (${status})`;
  if (status === 404) return `${label}: endpoint no encontrado`;
  if (status === 401 || status === 403) return `${label}: sesion sin permisos`;
  return `${label}: error ${status}`;
}

function App() {
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("demo@mktautomations.com");
  const [accessKey, setAccessKey] = useState("");
  const [projectIdFilter, setProjectIdFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [error, setError] = useState("");
  const [authError, setAuthError] = useState("");
  const [context, setContext] = useState<MeContext | null>(null);
  const [dashboard, setDashboard] = useState<MeDashboard | null>(null);
  const [costs, setCosts] = useState<CostSummary | null>(null);
  const [activeTab, setActiveTab] = useState<TabName>("overview");
  const [sourceStatus, setSourceStatus] = useState<SourceStatus>({
    context: "idle",
    dashboard: "idle",
    costs: "idle",
  });

  const projectCards = useMemo(() => context?.projects ?? [], [context]);
  const providerTotal = useMemo(
    () => (costs?.by_provider ?? []).reduce((acc, i) => acc + i.total_cost_usd, 0),
    [costs],
  );

  useEffect(() => {
    const storedToken = sessionStorage.getItem(SESSION_TOKEN_KEY);
    if (storedToken) {
      setToken(storedToken);
      void loadData(storedToken);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadData(providedToken?: string) {
    const currentToken = (providedToken ?? token).trim();
    if (!currentToken) return;

    setLoading(true);
    setError("");

    const headers = {
      Authorization: `Bearer ${currentToken}`,
      "Content-Type": "application/json",
    };

    const costUrl = projectIdFilter
      ? `${API_BASE_URL}/costs/summary?days=30&project_id=${projectIdFilter}`
      : `${API_BASE_URL}/costs/summary?days=30`;

    const [ctxRes, dashRes, costRes] = await Promise.allSettled([
      fetch(`${API_BASE_URL}/me/context`, { headers }),
      fetch(`${API_BASE_URL}/me/dashboard?limit=20`, { headers }),
      fetch(costUrl, { headers }),
    ]);

    try {
      const partialErrors: string[] = [];
      const nextStatus: SourceStatus = { context: "error", dashboard: "error", costs: "error" };

      if (ctxRes.status === "fulfilled") {
        if (ctxRes.value.status === 401 || ctxRes.value.status === 403) {
          logout();
          setError("Sesion expirada. Ingresa nuevamente.");
          return;
        }
        if (ctxRes.value.ok) {
          setContext((await ctxRes.value.json()) as MeContext);
          nextStatus.context = "ok";
        } else {
          partialErrors.push(humanError("Contexto", ctxRes.value.status));
        }
      } else {
        partialErrors.push("Contexto: no se pudo conectar con la API");
      }

      if (dashRes.status === "fulfilled") {
        if (dashRes.value.status === 401 || dashRes.value.status === 403) {
          logout();
          setError("Sesion expirada. Ingresa nuevamente.");
          return;
        }
        if (dashRes.value.ok) {
          setDashboard((await dashRes.value.json()) as MeDashboard);
          nextStatus.dashboard = "ok";
        } else {
          partialErrors.push(humanError("Dashboard", dashRes.value.status));
        }
      } else {
        partialErrors.push("Dashboard: no se pudo conectar con la API");
      }

      if (costRes.status === "fulfilled") {
        if (costRes.value.status === 401 || costRes.value.status === 403) {
          logout();
          setError("Sesion expirada. Ingresa nuevamente.");
          return;
        }
        if (costRes.value.ok) {
          setCosts((await costRes.value.json()) as CostSummary);
          nextStatus.costs = "ok";
        } else {
          partialErrors.push(humanError("Costos", costRes.value.status));
        }
      } else {
        partialErrors.push("Costos: no se pudo conectar con la API");
      }

      setSourceStatus(nextStatus);
      if (partialErrors.length > 0) {
        setError(`Vista parcial cargada. ${partialErrors.join(" | ")}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error";
      setError(`Error general al cargar datos: ${message}`);
    } finally {
      setLoading(false);
    }
  }

  async function loginWithEmail(e: FormEvent) {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), access_key: accessKey.trim() }),
      });
      if (!res.ok) {
        throw new Error(`Login error ${res.status}`);
      }
      const data = (await res.json()) as AuthTokenResponse;
      sessionStorage.setItem(SESSION_TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      setAccessKey("");
      await loadData(data.access_token);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error";
      setAuthError(message);
    } finally {
      setAuthLoading(false);
    }
  }

  function logout() {
    sessionStorage.removeItem(SESSION_TOKEN_KEY);
    setToken("");
    setContext(null);
    setDashboard(null);
    setCosts(null);
    setError("");
    setAuthError("");
    setActiveTab("overview");
    setSourceStatus({ context: "idle", dashboard: "idle", costs: "idle" });
  }

  if (!token) {
    return (
      <section className="auth-screen">
        <div className="auth-particles" aria-hidden="true" />
        <div className="auth-card">
          <article className="auth-form-side">
            <div className="auth-mini-brand">
              <img src="/automationia-logo.svg" alt="automationIA" className="auth-mini-mark-logo" />
              <span>mktautomations platform</span>
            </div>
            <h1>Acceder</h1>
            <p>Ingresa para gestionar proyectos, agentes y costos con inteligencia operativa.</p>
            <form onSubmit={loginWithEmail} className="stack">
              <label htmlFor="email">Correo electronico</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="usuario@empresa.com"
                required
              />
              <label htmlFor="accessKey">Clave de acceso</label>
              <input
                id="accessKey"
                type="password"
                value={accessKey}
                onChange={(e) => setAccessKey(e.target.value)}
                placeholder="Clave interna"
                required
              />
              <button type="submit" disabled={authLoading || !email || !accessKey}>
                {authLoading ? "Ingresando..." : "Iniciar sesion"}
              </button>
            </form>
            <p className="auth-help">Acceso interno. Si no tienes permisos, solicita alta de usuario.</p>
            {authError ? <p className="error">{authError}</p> : null}
          </article>
          <article className="auth-brand-side">
            <img src="/automationia-logo.svg" alt="automationIA logo" className="auth-main-logo" />
            <p className="tag">Plataforma IA</p>
            <h2>WELCOME BACK!</h2>
            <p>Panel operativo de proyectos, agentes y costos en tiempo real.</p>
            <img
              src="/automationia-logo-horizontal.svg"
              alt="automationIA horizontal logo"
              className="auth-horizontal-logo"
            />
          </article>
        </div>
      </section>
    );
  }

  return (
    <div className="platform-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/automationia-logo-icon.svg" alt="automationIA icon" className="brand-mark-image" />
          <div>
            <h1>automationIA</h1>
            <p>Project Control Center</p>
          </div>
        </div>

        <nav className="menu">
          <button className={activeTab === "overview" ? "active" : ""} onClick={() => setActiveTab("overview")}>
            Overview
          </button>
          <button className={activeTab === "projects" ? "active" : ""} onClick={() => setActiveTab("projects")}>
            Projects
          </button>
          <button className={activeTab === "costs" ? "active" : ""} onClick={() => setActiveTab("costs")}>
            Costs
          </button>
          <button className={activeTab === "ideas" ? "active" : ""} onClick={() => setActiveTab("ideas")}>
            Ideas
          </button>
          <button className={activeTab === "agents" ? "active" : ""} onClick={() => setActiveTab("agents")}>
            Agents
          </button>
        </nav>

        <div className="sidebar-footer">
          {context?.profile ? (
            <>
              <p>{context.profile.email ?? "Sin email"}</p>
              <button className="ghost" onClick={logout}>
                Cerrar sesion
              </button>
            </>
          ) : (
            <p>No autenticado</p>
          )}
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <h2>Plataforma IA Control Center</h2>
            <p>Vista ejecutiva para operar proyectos, agentes y costos de IA.</p>
          </div>
          <div className="topbar-actions">
            <span className={`status-dot ${loading ? "is-loading" : "is-ready"}`}>{loading ? "Sincronizando" : "Online"}</span>
            <button className="refresh" onClick={() => void loadData()} disabled={loading}>
              {loading ? "Actualizando..." : "Actualizar"}
            </button>
          </div>
        </header>

        <section className="source-status-grid">
          <article className={`source-chip ${sourceStatus.context}`}>
            <span>Contexto</span>
            <b>{sourceStatus.context.toUpperCase()}</b>
          </article>
          <article className={`source-chip ${sourceStatus.dashboard}`}>
            <span>Dashboard</span>
            <b>{sourceStatus.dashboard.toUpperCase()}</b>
          </article>
          <article className={`source-chip ${sourceStatus.costs}`}>
            <span>Costos</span>
            <b>{sourceStatus.costs.toUpperCase()}</b>
          </article>
        </section>

        {error ? <p className="error floating-error">{error}</p> : null}

        {activeTab === "overview" ? (
          <>
            <section className="kpi-grid">
              <article className="panel kpi-card">
                <span>Proyectos activos</span>
                <strong>{dashboard?.kpis.projects_count ?? projectCards.length ?? 0}</strong>
              </article>
              <article className="panel kpi-card">
                <span>Etapas bloqueadas</span>
                <strong>{dashboard?.kpis.blocked_stages_count ?? 0}</strong>
              </article>
              <article className="panel kpi-card">
                <span>Runs fallidas (7d)</span>
                <strong>{dashboard?.kpis.failed_runs_count_7d ?? 0}</strong>
              </article>
              <article className="panel kpi-card">
                <span>Costo IA (30d)</span>
                <strong>{formatCurrency(dashboard?.kpis.cost_usd_total_30d ?? costs?.total_cost_usd ?? 0)}</strong>
              </article>
            </section>

            <section className="split-grid">
              <article className="panel">
                <h4>Pipeline de proyectos</h4>
                {projectCards.length ? (
                  <table>
                    <thead>
                      <tr>
                        <th>Proyecto</th>
                        <th>Rol</th>
                        <th>Estado</th>
                        <th>Actualizado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {projectCards.map((p) => (
                        <tr key={p.project_id}>
                          <td>
                            <strong>{p.project_key}</strong>
                            <br />
                            {p.project_name}
                          </td>
                          <td>{p.member_role}</td>
                          <td>{p.lifecycle_status}</td>
                          <td>{formatDate(p.updated_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="subtle">Sin proyectos visibles para este usuario.</p>
                )}
              </article>

              <article className="panel">
                <h4>Distribucion de costos por proveedor</h4>
                {costs?.by_provider?.length ? (
                  <div className="provider-bars">
                    {costs.by_provider.map((item) => {
                      const width = providerTotal > 0 ? (item.total_cost_usd / providerTotal) * 100 : 0;
                      return (
                        <div key={item.provider} className="provider-row">
                          <div className="provider-top">
                            <span>{item.provider}</span>
                            <span>{formatCurrency(item.total_cost_usd)}</span>
                          </div>
                          <div className="bar-track">
                            <div className="bar-fill" style={{ width: `${Math.max(width, 3)}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="subtle">Sin costos disponibles en el periodo.</p>
                )}
              </article>
            </section>
          </>
        ) : null}

        {activeTab === "projects" ? (
          <section className="cards-2">
            {projectCards.map((project) => (
              <article className="panel project-tile" key={project.project_id}>
                <h4>{project.project_name}</h4>
                <p>{project.project_key}</p>
                <div className="tile-meta">
                  <span>Rol: {project.member_role}</span>
                  <span>Estado: {project.lifecycle_status}</span>
                </div>
                <small>Actualizado: {formatDate(project.updated_at)}</small>
              </article>
            ))}
            {!projectCards.length ? (
              <article className="panel">
                <p>No hay proyectos para mostrar.</p>
              </article>
            ) : null}
          </section>
        ) : null}

        {activeTab === "costs" ? (
          <section className="cards-2">
            <article className="panel">
              <h4>Filtro de costos</h4>
              <div className="inline">
                <input
                  value={projectIdFilter}
                  onChange={(e) => setProjectIdFilter(e.target.value)}
                  placeholder="Project ID (opcional)"
                />
                <button onClick={() => void loadData()} disabled={loading}>
                  Recalcular
                </button>
              </div>
            </article>
            <article className="panel">
              <h4>Resumen economico</h4>
              <p className="total">
                Total 30d: <b>{formatCurrency(costs?.total_cost_usd ?? 0)}</b>
              </p>
              <p className="subtle">Runs: {costs?.total_runs_count ?? 0}</p>
            </article>
          </section>
        ) : null}

        {activeTab === "ideas" ? (
          <section className="cards-2">
            <article className="panel coming-soon">
              <h4>Ideas Lab</h4>
              <p>Modulo para capturar, priorizar y convertir ideas en proyectos ejecutables.</p>
              <ul className="flags">
                <li>Captura estructurada de idea</li>
                <li>Scoring de impacto y esfuerzo</li>
                <li>Boton convertir a proyecto</li>
              </ul>
            </article>
          </section>
        ) : null}

        {activeTab === "agents" ? (
          <section className="cards-2">
            <article className="panel coming-soon">
              <h4>Agent Operations</h4>
              <p>Modulo para operar agentes por etapa, trazabilidad y costo por salida.</p>
              <ul className="flags">
                <li>Catalogo por modulo y proveedor</li>
                <li>Monitoreo de ejecuciones</li>
                <li>Calidad y costo por agente</li>
              </ul>
            </article>
          </section>
        ) : null}
      </main>
    </div>
  );
}

export default App;
