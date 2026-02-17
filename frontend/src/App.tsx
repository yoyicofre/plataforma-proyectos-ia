import "./App.css";
import { useEffect, useState } from "react";
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
};

type CostSummary = {
  total_cost_usd: number;
  total_runs_count: number;
  by_provider: Array<{ provider: string; total_cost_usd: number; runs_count: number }>;
};

type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
};

type TabName = "overview" | "projects" | "costs" | "ideas" | "agents";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const SESSION_TOKEN_KEY = "plataforma_ia_access_token";

function App() {
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
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
    try {
      const headers = {
        Authorization: `Bearer ${currentToken}`,
        "Content-Type": "application/json",
      };
      const contextRes = await fetch(`${API_BASE_URL}/me/context`, { headers });
      if (!contextRes.ok) throw new Error(`Context error ${contextRes.status}`);

      const dashboardRes = await fetch(`${API_BASE_URL}/me/dashboard?limit=20`, { headers });
      if (!dashboardRes.ok) throw new Error(`Dashboard error ${dashboardRes.status}`);

      const costUrl = projectIdFilter
        ? `${API_BASE_URL}/costs/summary?days=30&project_id=${projectIdFilter}`
        : `${API_BASE_URL}/costs/summary?days=30`;
      const costRes = await fetch(costUrl, { headers });
      if (!costRes.ok) throw new Error(`Costs error ${costRes.status}`);

      setContext((await contextRes.json()) as MeContext);
      setDashboard((await dashboardRes.json()) as MeDashboard);
      setCosts((await costRes.json()) as CostSummary);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error";
      setError(message);
      if (message.includes("401") || message.includes("403")) {
        sessionStorage.removeItem(SESSION_TOKEN_KEY);
        setToken("");
      }
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
  }

  if (!token) {
    return (
      <section className="auth-screen">
        <div className="auth-card">
          <article className="auth-form-side">
            <h1>Acceder</h1>
            <p>Bienvenido de nuevo. Ingresa para entrar a tu panel.</p>
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
            {authError ? <p className="error">{authError}</p> : null}
          </article>
          <article className="auth-brand-side">
            <p className="tag">Plataforma IA</p>
            <h2>WELCOME BACK!</h2>
            <p>Panel operativo de proyectos, agentes y costos en tiempo real.</p>
          </article>
        </div>
      </section>
    );
  }

  return (
    <div className="platform-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">IA</div>
          <div>
            <h1>Plataforma IA</h1>
            <p>Control Center</p>
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
            <p>Vision operativa de proyectos, agentes y costos en tiempo real.</p>
          </div>
          {token ? (
            <button className="refresh" onClick={() => void loadData()} disabled={loading}>
              {loading ? "Actualizando..." : "Actualizar"}
            </button>
          ) : null}
        </header>

        <>
            {activeTab === "overview" ? (
              <section className="cards-3">
                <article className="panel metric">
                  <h4>Perfil</h4>
                  {context ? (
                    <div className="kv">
                      <p><strong>User ID:</strong> {context.profile.user_id}</p>
                      <p><strong>Email:</strong> {context.profile.email ?? "-"}</p>
                      <p><strong>Roles:</strong> {context.profile.roles.join(", ")}</p>
                    </div>
                  ) : (
                    <p>Sin datos</p>
                  )}
                </article>
                <article className="panel metric">
                  <h4>Permisos globales</h4>
                  {context ? (
                    <ul className="flags">
                      <li>Acceso plataforma: {String(context.global_permissions.can_access_platform)}</li>
                      <li>Crear proyectos: {String(context.global_permissions.can_create_projects)}</li>
                      <li>Gestionar agentes: {String(context.global_permissions.can_manage_agent_catalog)}</li>
                      <li>Gestionar seguridad: {String(context.global_permissions.can_manage_security)}</li>
                    </ul>
                  ) : (
                    <p>Sin datos</p>
                  )}
                </article>
                <article className="panel metric">
                  <h4>KPIs (30 dias)</h4>
                  {dashboard ? (
                    <ul className="kpi-list">
                      <li><span>Proyectos</span><b>{dashboard.kpis.projects_count}</b></li>
                      <li><span>Etapas bloqueadas</span><b>{dashboard.kpis.blocked_stages_count}</b></li>
                      <li><span>Runs fallidas (7d)</span><b>{dashboard.kpis.failed_runs_count_7d}</b></li>
                      <li><span>Runs en cola</span><b>{dashboard.kpis.queued_runs_count}</b></li>
                      <li><span>Artifacts publicados</span><b>{dashboard.kpis.published_artifacts_count}</b></li>
                      <li><span>Costo IA</span><b>${dashboard.kpis.cost_usd_total_30d.toFixed(4)}</b></li>
                    </ul>
                  ) : (
                    <p>Sin datos</p>
                  )}
                </article>
              </section>
            ) : null}

            {activeTab === "projects" ? (
              <section className="cards-2">
                <article className="panel">
                  <h4>Proyectos visibles</h4>
                  {context?.projects?.length ? (
                    <table>
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Key</th>
                          <th>Nombre</th>
                          <th>Rol</th>
                          <th>Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {context.projects.map((p) => (
                          <tr key={p.project_id}>
                            <td>{p.project_id}</td>
                            <td>{p.project_key}</td>
                            <td>{p.project_name}</td>
                            <td>{p.member_role}</td>
                            <td>{p.lifecycle_status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p>No hay proyectos asignados.</p>
                  )}
                </article>
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
                  <h4>Costos por proveedor</h4>
                  {costs ? (
                    <>
                      <p className="total">
                        Total: <b>${costs.total_cost_usd.toFixed(6)}</b> en {costs.total_runs_count} runs
                      </p>
                      <table>
                        <thead>
                          <tr>
                            <th>Proveedor</th>
                            <th>Runs</th>
                            <th>Costo USD</th>
                          </tr>
                        </thead>
                        <tbody>
                          {costs.by_provider.map((item) => (
                            <tr key={item.provider}>
                              <td>{item.provider}</td>
                              <td>{item.runs_count}</td>
                              <td>${item.total_cost_usd.toFixed(6)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </>
                  ) : (
                    <p>Sin costos</p>
                  )}
                </article>
              </section>
            ) : null}

            {activeTab === "ideas" ? (
              <section className="cards-2">
                <article className="panel">
                  <h4>Ideas Workspace</h4>
                  <p className="subtle">Proximo modulo: captura de ideas, priorizacion y conversion a proyecto.</p>
                  <ul className="flags">
                    <li>Formulario de idea con impacto y prioridad</li>
                    <li>Estados: nueva, evaluacion, aprobada, en_proyecto</li>
                    <li>Boton: Convertir idea a proyecto</li>
                  </ul>
                </article>
              </section>
            ) : null}

            {activeTab === "agents" ? (
              <section className="cards-2">
                <article className="panel">
                  <h4>Agent Operations</h4>
                  <p className="subtle">Proximo modulo: health de agentes, runs, errores y productividad por modulo.</p>
                  <ul className="flags">
                    <li>Catalogo de agentes por dominio</li>
                    <li>Rendimiento por etapa</li>
                    <li>Trazabilidad de errores y retrys</li>
                  </ul>
                </article>
              </section>
            ) : null}
        </>

        {error && <p className="error floating-error">{error}</p>}
      </main>
    </div>
  );
}

export default App;
