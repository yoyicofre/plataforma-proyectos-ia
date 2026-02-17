import { useMemo, useState } from "react";
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
  by_model: Array<{ provider: string | null; model_name: string | null; total_cost_usd: number }>;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function App() {
  const [token, setToken] = useState("");
  const [projectIdFilter, setProjectIdFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [context, setContext] = useState<MeContext | null>(null);
  const [dashboard, setDashboard] = useState<MeDashboard | null>(null);
  const [costs, setCosts] = useState<CostSummary | null>(null);

  const headers = useMemo(
    () => ({
      Authorization: `Bearer ${token.trim()}`,
      "Content-Type": "application/json",
    }),
    [token],
  );

  async function loadData(e?: FormEvent) {
    e?.preventDefault();
    setLoading(true);
    setError("");
    try {
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
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <h1>Plataforma IA Control Center</h1>
        <p>Vision operativa de proyectos, agentes y costos en tiempo real.</p>
      </header>

      <form className="panel auth-panel" onSubmit={loadData}>
        <label htmlFor="token">JWT Token</label>
        <textarea
          id="token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Pega aquí tu Bearer token"
          rows={4}
        />
        <div className="inline-fields">
          <div>
            <label htmlFor="projectIdFilter">Project ID (opcional para costos)</label>
            <input
              id="projectIdFilter"
              value={projectIdFilter}
              onChange={(e) => setProjectIdFilter(e.target.value)}
              placeholder="ej: 8"
            />
          </div>
          <button type="submit" disabled={loading || !token.trim()}>
            {loading ? "Cargando..." : "Cargar panel"}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </form>

      <section className="grid">
        <article className="panel">
          <h2>Perfil</h2>
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

        <article className="panel">
          <h2>Permisos globales</h2>
          {context ? (
            <ul className="flags">
              <li>Acceso plataforma: {String(context.global_permissions.can_access_platform)}</li>
              <li>Crear proyectos: {String(context.global_permissions.can_create_projects)}</li>
              <li>Gestionar agentes: {String(context.global_permissions.can_manage_agent_catalog)}</li>
              <li>Emitir tokens dev: {String(context.global_permissions.can_issue_dev_tokens)}</li>
              <li>Gestionar seguridad: {String(context.global_permissions.can_manage_security)}</li>
            </ul>
          ) : (
            <p>Sin datos</p>
          )}
        </article>

        <article className="panel">
          <h2>KPIs (30 días)</h2>
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

      <section className="grid two">
        <article className="panel">
          <h2>Proyectos visibles</h2>
          {context?.projects?.length ? (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Key</th>
                  <th>Nombre</th>
                  <th>Rol</th>
                </tr>
              </thead>
              <tbody>
                {context.projects.map((p) => (
                  <tr key={p.project_id}>
                    <td>{p.project_id}</td>
                    <td>{p.project_key}</td>
                    <td>{p.project_name}</td>
                    <td>{p.member_role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>Sin proyectos</p>
          )}
        </article>

        <article className="panel">
          <h2>Costos por proveedor</h2>
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
    </div>
  );
}

export default App;
