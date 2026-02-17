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

type ProjectItem = {
  project_id: number;
  project_key: string;
  project_name: string;
  description: string | null;
  lifecycle_status: string;
  owner_user_id: number;
  created_at: string;
  updated_at: string;
};

type AgentItem = {
  agent_id: number;
  agent_code: string;
  agent_name: string;
  module_name: string;
  owner_team: string;
  default_model: string | null;
  skill_ref: string | null;
  is_active: boolean;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

type AgentRunItem = {
  agent_run_id: number;
  project_id: number;
  agent_id: number;
  provider: string | null;
  model_name: string | null;
  run_status: string;
  trigger_source: string;
  duration_ms: number | null;
  cost_usd: number | null;
  created_at: string;
};

type StageItem = {
  project_stage_status_id: number;
  project_id: number;
  stage_id: number;
  stage_code: string;
  stage_name: string;
  stage_order: number;
  stage_status: string;
  progress_percent: number;
  updated_at: string;
};

type ProjectAgentAssignment = {
  project_agent_assignment_id: number;
  project_id: number;
  agent_id: number;
  stage_id: number | null;
  assignment_status: string;
  assigned_at: string;
};

type AiTextGenerateResponse = {
  run_id: number;
  provider: string;
  model_name: string;
  text: string;
  token_input_count: number | null;
  token_output_count: number | null;
  cost_usd: number | null;
};

type AiImageGenerateResponse = {
  run_id: number;
  provider: string;
  model_name: string;
  mime_type: string | null;
  image_base64: string | null;
  image_url: string | null;
  cost_usd: number | null;
};

type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
};

type TextIaMessage = {
  role: "user" | "assistant";
  content: string;
  runId?: number;
  provider?: string;
  model?: string;
  costUsd?: number | null;
};

type IaConversationOut = {
  conversation_id: number;
  project_id: number;
  agent_id: number;
  title: string | null;
  status: string;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
};

type IaSavedOutputOut = {
  saved_output_id: number;
  conversation_id: number;
  message_id: number;
  label: string;
  notes: string | null;
  created_by_user_id: number;
  created_at: string;
  project_id: number;
  agent_id: number;
  run_id: number | null;
  provider: string | null;
  model_name: string | null;
  content: string;
};

type TabName = "overview" | "projects" | "costs" | "ideas" | "agents" | "ia_generator";
type SourceName = "context" | "dashboard" | "costs";
type SourceStatus = Record<SourceName, "idle" | "ok" | "error">;
type ApiStatus = "unknown" | "online" | "offline";

const SESSION_TOKEN_KEY = "plataforma_ia_access_token";

function resolveApiBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
  if (envUrl) return envUrl.replace(/\/+$/, "");

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    if (hostname.startsWith("app.")) {
      return `${protocol}//api.${hostname.slice(4)}`;
    }
  }

  return "http://127.0.0.1:8000";
}

const API_BASE_URL = resolveApiBaseUrl();

function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

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
  const [apiStatus, setApiStatus] = useState<ApiStatus>("unknown");
  const [sourceStatus, setSourceStatus] = useState<SourceStatus>({
    context: "idle",
    dashboard: "idle",
    costs: "idle",
  });
  const [projectsData, setProjectsData] = useState<ProjectItem[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [projectError, setProjectError] = useState("");
  const [newProjectKey, setNewProjectKey] = useState("");
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectStatus, setNewProjectStatus] = useState("draft");

  const [agentsData, setAgentsData] = useState<AgentItem[]>([]);
  const [agentsLoading, setAgentsLoading] = useState(false);
  const [agentsError, setAgentsError] = useState("");
  const [newAgentCode, setNewAgentCode] = useState("");
  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentModule, setNewAgentModule] = useState("planning");
  const [newAgentTeam, setNewAgentTeam] = useState("Automation");
  const [newAgentModel, setNewAgentModel] = useState("gpt-5.2");

  const [assignments, setAssignments] = useState<ProjectAgentAssignment[]>([]);
  const [assignmentProjectId, setAssignmentProjectId] = useState("");
  const [assignmentAgentId, setAssignmentAgentId] = useState("");
  const [assignmentError, setAssignmentError] = useState("");

  const [execProjectId, setExecProjectId] = useState("");
  const [execAgentId, setExecAgentId] = useState("");
  const [execProvider, setExecProvider] = useState("auto");
  const [execModel, setExecModel] = useState("");
  const [execPrompt, setExecPrompt] = useState("");
  const [execSystemPrompt, setExecSystemPrompt] = useState("");
  const [execLoading, setExecLoading] = useState(false);
  const [execError, setExecError] = useState("");
  const [execResult, setExecResult] = useState<AiTextGenerateResponse | null>(null);

  const [imgProjectId, setImgProjectId] = useState("");
  const [imgAgentId, setImgAgentId] = useState("");
  const [imgProvider, setImgProvider] = useState("auto");
  const [imgModel, setImgModel] = useState("");
  const [imgSize, setImgSize] = useState("1024x1024");
  const [imgPrompt, setImgPrompt] = useState("");
  const [imgLoading, setImgLoading] = useState(false);
  const [imgError, setImgError] = useState("");
  const [imgResult, setImgResult] = useState<AiImageGenerateResponse | null>(null);

  const [iaProjectId, setIaProjectId] = useState("");
  const [iaAgentId, setIaAgentId] = useState("");
  const [iaProvider, setIaProvider] = useState("auto");
  const [iaModel, setIaModel] = useState("");
  const [iaSystemPrompt, setIaSystemPrompt] = useState("");
  const [iaPrompt, setIaPrompt] = useState("");
  const [iaMessages, setIaMessages] = useState<TextIaMessage[]>([]);
  const [iaConversationId, setIaConversationId] = useState<number | null>(null);
  const [iaSavedOutputs, setIaSavedOutputs] = useState<IaSavedOutputOut[]>([]);
  const [iaSavedLoading, setIaSavedLoading] = useState(false);
  const [iaLoading, setIaLoading] = useState(false);
  const [iaError, setIaError] = useState("");

  const [runsData, setRunsData] = useState<AgentRunItem[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [runsError, setRunsError] = useState("");

  const [stageProjectId, setStageProjectId] = useState("");
  const [stagesData, setStagesData] = useState<StageItem[]>([]);
  const [stagesLoading, setStagesLoading] = useState(false);
  const [stagesError, setStagesError] = useState("");

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

  const buildAuthHeaders = (currentToken: string) => ({
    Authorization: `Bearer ${currentToken}`,
    "Content-Type": "application/json",
  });

  async function loadProjects(providedToken?: string) {
    const currentToken = (providedToken ?? token).trim();
    if (!currentToken) return;
    setProjectsLoading(true);
    setProjectError("");
    try {
      const res = await fetch(apiUrl("/projects/?limit=100"), { headers: buildAuthHeaders(currentToken) });
      if (!res.ok) throw new Error(`projects ${res.status}`);
      setProjectsData((await res.json()) as ProjectItem[]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setProjectError(message);
    } finally {
      setProjectsLoading(false);
    }
  }

  async function loadAgents(providedToken?: string) {
    const currentToken = (providedToken ?? token).trim();
    if (!currentToken) return;
    setAgentsLoading(true);
    setAgentsError("");
    try {
      const [agentsRes, assignmentsRes] = await Promise.all([
        fetch(apiUrl("/agents/?limit=100"), { headers: buildAuthHeaders(currentToken) }),
        fetch(apiUrl("/project-agent-assignments/?limit=100"), { headers: buildAuthHeaders(currentToken) }),
      ]);
      if (!agentsRes.ok) throw new Error(`agents ${agentsRes.status}`);
      if (!assignmentsRes.ok) throw new Error(`assignments ${assignmentsRes.status}`);
      setAgentsData((await agentsRes.json()) as AgentItem[]);
      setAssignments((await assignmentsRes.json()) as ProjectAgentAssignment[]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setAgentsError(message);
    } finally {
      setAgentsLoading(false);
    }
  }

  async function loadRuns(providedToken?: string) {
    const currentToken = (providedToken ?? token).trim();
    if (!currentToken) return;
    setRunsLoading(true);
    setRunsError("");
    try {
      const runsUrl = projectIdFilter
        ? apiUrl(`/agent-runs/?limit=20&project_id=${projectIdFilter}`)
        : apiUrl("/agent-runs/?limit=20");
      const res = await fetch(runsUrl, { headers: buildAuthHeaders(currentToken) });
      if (!res.ok) throw new Error(`agent-runs ${res.status}`);
      setRunsData((await res.json()) as AgentRunItem[]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setRunsError(message);
    } finally {
      setRunsLoading(false);
    }
  }

  async function loadStages(projectIdRaw: string, providedToken?: string) {
    const currentToken = (providedToken ?? token).trim();
    const projectId = projectIdRaw.trim();
    if (!currentToken || !projectId) return;
    setStagesLoading(true);
    setStagesError("");
    try {
      const res = await fetch(apiUrl(`/projects/${projectId}/stages`), { headers: buildAuthHeaders(currentToken) });
      if (!res.ok) throw new Error(`stages ${res.status}`);
      setStagesData((await res.json()) as StageItem[]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setStagesError(message);
    } finally {
      setStagesLoading(false);
    }
  }

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
      ? apiUrl(`/costs/summary?days=30&project_id=${projectIdFilter}`)
      : apiUrl("/costs/summary?days=30");

    try {
      const healthRes = await fetch(apiUrl("/health"));
      setApiStatus(healthRes.ok ? "online" : "offline");
    } catch {
      setApiStatus("offline");
    }

    const [ctxRes, dashRes, costRes] = await Promise.allSettled([
      fetch(apiUrl("/me/context"), { headers }),
      fetch(apiUrl("/me/dashboard?limit=20"), { headers }),
      fetch(costUrl, { headers }),
    ]);

    try {
      const partialErrors: string[] = [];
      const nextStatus: SourceStatus = { context: "error", dashboard: "error", costs: "error" };

      if (ctxRes.status === "fulfilled") {
        if (ctxRes.value.status === 401 || ctxRes.value.status === 403) {
          await logout();
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
          await logout();
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
          await logout();
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
      setApiStatus("offline");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token) return;
    if (activeTab === "projects") {
      void loadProjects();
    } else if (activeTab === "agents") {
      void loadAgents();
      if (projectsData.length === 0) {
        void loadProjects();
      }
    } else if (activeTab === "costs") {
      void loadRuns();
    } else if (activeTab === "ideas" && projectsData.length === 0) {
      void loadProjects();
    } else if (activeTab === "ia_generator") {
      if (projectsData.length === 0) {
        void loadProjects();
      }
      if (agentsData.length === 0) {
        void loadAgents();
      }
      void loadIaSavedOutputs();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, token]);

  useEffect(() => {
    if (!token || activeTab !== "ia_generator") return;
    setIaConversationId(null);
    void loadIaSavedOutputs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [iaProjectId, iaAgentId]);

  async function loginWithEmail(e: FormEvent) {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");
    try {
      const res = await fetch(apiUrl("/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), access_key: accessKey.trim() }),
      });
      if (!res.ok) {
        throw new Error(`Login error ${res.status}`);
      }
      const data = (await res.json()) as AuthTokenResponse;
      setApiStatus("online");
      sessionStorage.setItem(SESSION_TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      setAccessKey("");
      await loadData(data.access_token);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error";
      setAuthError(message);
      setApiStatus("offline");
    } finally {
      setAuthLoading(false);
    }
  }

  async function createProject() {
    const currentToken = token.trim();
    if (!currentToken || !newProjectKey.trim() || !newProjectName.trim()) return;
    setProjectError("");
    try {
      const res = await fetch(apiUrl("/projects/"), {
        method: "POST",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          project_key: newProjectKey.trim(),
          project_name: newProjectName.trim(),
          lifecycle_status: newProjectStatus,
        }),
      });
      if (!res.ok) throw new Error(`create-project ${res.status}`);
      setNewProjectKey("");
      setNewProjectName("");
      setNewProjectStatus("draft");
      await Promise.all([loadProjects(), loadData()]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setProjectError(message);
    }
  }

  async function createAgent() {
    const currentToken = token.trim();
    if (!currentToken || !newAgentCode.trim() || !newAgentName.trim()) return;
    setAgentsError("");
    try {
      const res = await fetch(apiUrl("/agents/"), {
        method: "POST",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          agent_code: newAgentCode.trim(),
          agent_name: newAgentName.trim(),
          module_name: newAgentModule.trim(),
          owner_team: newAgentTeam.trim(),
          default_model: newAgentModel.trim() || null,
          is_active: true,
        }),
      });
      if (!res.ok) throw new Error(`create-agent ${res.status}`);
      setNewAgentCode("");
      setNewAgentName("");
      await loadAgents();
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setAgentsError(message);
    }
  }

  async function assignAgentToProject() {
    const currentToken = token.trim();
    if (!currentToken || !assignmentProjectId.trim() || !assignmentAgentId.trim()) return;
    setAssignmentError("");
    try {
      const res = await fetch(apiUrl("/project-agent-assignments/"), {
        method: "POST",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          project_id: Number(assignmentProjectId),
          agent_id: Number(assignmentAgentId),
          assignment_status: "active",
        }),
      });
      if (!res.ok) throw new Error(`assign-agent ${res.status}`);
      setAssignmentProjectId("");
      setAssignmentAgentId("");
      await loadAgents();
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setAssignmentError(message);
    }
  }

  async function executeAgentText() {
    const currentToken = token.trim();
    if (!currentToken || !execProjectId.trim() || !execAgentId.trim() || !execPrompt.trim()) return;

    setExecLoading(true);
    setExecError("");
    setExecResult(null);

    try {
      const res = await fetch(apiUrl("/ai/text/generate"), {
        method: "POST",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          project_id: Number(execProjectId),
          agent_id: Number(execAgentId),
          prompt: execPrompt.trim(),
          system_prompt: execSystemPrompt.trim() || null,
          provider_preference: execProvider,
          model_name: execModel.trim() || null,
        }),
      });
      if (!res.ok) throw new Error(`execute-agent ${res.status}`);
      const data = (await res.json()) as AiTextGenerateResponse;
      setExecResult(data);

      await Promise.all([loadData(), loadRuns(), loadAgents()]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setExecError(message);
    } finally {
      setExecLoading(false);
    }
  }

  async function loadIaSavedOutputs(providedToken?: string) {
    const currentToken = (providedToken ?? token).trim();
    if (!currentToken) return;
    setIaSavedLoading(true);
    try {
      const query = new URLSearchParams();
      query.set("limit", "30");
      if (iaProjectId) query.set("project_id", iaProjectId);
      if (iaAgentId) query.set("agent_id", iaAgentId);
      const res = await fetch(apiUrl(`/ia/saved-outputs?${query.toString()}`), {
        headers: buildAuthHeaders(currentToken),
      });
      if (!res.ok) throw new Error(`ia-saved ${res.status}`);
      setIaSavedOutputs((await res.json()) as IaSavedOutputOut[]);
    } catch {
      setIaSavedOutputs([]);
    } finally {
      setIaSavedLoading(false);
    }
  }

  async function ensureIaConversation(providedToken?: string): Promise<number> {
    const currentToken = (providedToken ?? token).trim();
    if (!currentToken) throw new Error("Missing token");
    if (iaConversationId) return iaConversationId;
    if (!iaProjectId || !iaAgentId) throw new Error("Selecciona proyecto y agente");

    const res = await fetch(apiUrl("/ia/conversations"), {
      method: "POST",
      headers: buildAuthHeaders(currentToken),
      body: JSON.stringify({
        project_id: Number(iaProjectId),
        agent_id: Number(iaAgentId),
        title: `Text IA ${new Date().toISOString()}`,
      }),
    });
    if (!res.ok) throw new Error(`ia-conversation ${res.status}`);
    const data = (await res.json()) as IaConversationOut;
    setIaConversationId(data.conversation_id);
    return data.conversation_id;
  }

  async function executeAgentImage() {
    const currentToken = token.trim();
    if (!currentToken || !imgProjectId.trim() || !imgAgentId.trim() || !imgPrompt.trim()) return;

    setImgLoading(true);
    setImgError("");
    setImgResult(null);

    try {
      const res = await fetch(apiUrl("/ai/image/generate"), {
        method: "POST",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          project_id: Number(imgProjectId),
          agent_id: Number(imgAgentId),
          prompt: imgPrompt.trim(),
          provider_preference: imgProvider,
          model_name: imgModel.trim() || null,
          size: imgSize.trim() || "1024x1024",
        }),
      });
      if (!res.ok) throw new Error(`execute-image ${res.status}`);
      const data = (await res.json()) as AiImageGenerateResponse;
      setImgResult(data);

      await Promise.all([loadData(), loadRuns(), loadAgents()]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setImgError(message);
    } finally {
      setImgLoading(false);
    }
  }

  async function runTextIaIteration() {
    const currentToken = token.trim();
    if (!currentToken || !iaProjectId.trim() || !iaAgentId.trim() || !iaPrompt.trim()) return;

    const userMessage: TextIaMessage = { role: "user", content: iaPrompt.trim() };
    const history = [...iaMessages, userMessage]
      .slice(-8)
      .map((m) => `${m.role === "user" ? "Usuario" : "Asistente"}: ${m.content}`)
      .join("\n");
    const promptForModel = `Conversacion previa:\n${history}\n\nMensaje actual del usuario:\n${iaPrompt.trim()}`;

    setIaLoading(true);
    setIaError("");
    setIaMessages((prev) => [...prev, userMessage]);

    try {
      const res = await fetch(apiUrl("/ai/text/generate"), {
        method: "POST",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          project_id: Number(iaProjectId),
          agent_id: Number(iaAgentId),
          prompt: promptForModel,
          system_prompt: iaSystemPrompt.trim() || null,
          provider_preference: iaProvider,
          model_name: iaModel.trim() || null,
        }),
      });
      if (!res.ok) throw new Error(`text-ia ${res.status}`);
      const data = (await res.json()) as AiTextGenerateResponse;

      setIaMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.text || "(sin respuesta)",
          runId: data.run_id,
          provider: data.provider,
          model: data.model_name,
          costUsd: data.cost_usd,
        },
      ]);
      setIaPrompt("");
      await Promise.all([loadData(), loadRuns()]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setIaError(message);
    } finally {
      setIaLoading(false);
    }
  }

  async function saveIaIteration(messageIndex: number) {
    const currentToken = token.trim();
    if (!currentToken) return;
    const message = iaMessages[messageIndex];
    if (!message || message.role !== "assistant") return;

    const label = window.prompt("Etiqueta para guardar esta iteracion:", "Iteracion IA");
    if (!label || !label.trim()) return;
    const notes = window.prompt("Notas (opcional):", "") ?? "";

    try {
      const conversationId = await ensureIaConversation(currentToken);
      const previousUser =
        iaMessages
          .slice(0, messageIndex)
          .reverse()
          .find((m) => m.role === "user")?.content ?? null;

      if (previousUser) {
        await fetch(apiUrl(`/ia/conversations/${conversationId}/messages`), {
          method: "POST",
          headers: buildAuthHeaders(currentToken),
          body: JSON.stringify({
            role: "user",
            content: previousUser,
          }),
        });
      }

      const assistantRes = await fetch(apiUrl(`/ia/conversations/${conversationId}/messages`), {
        method: "POST",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          role: "assistant",
          content: message.content,
          provider: message.provider ?? null,
          model_name: message.model ?? null,
          run_id: message.runId ?? null,
          cost_usd: message.costUsd ?? null,
        }),
      });
      if (!assistantRes.ok) throw new Error(`save-message ${assistantRes.status}`);
      const assistantMsg = (await assistantRes.json()) as { message_id: number };

      const saveRes = await fetch(apiUrl(`/ia/messages/${assistantMsg.message_id}/save`), {
        method: "POST",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          label: label.trim(),
          notes: notes.trim() || null,
        }),
      });
      if (!saveRes.ok) throw new Error(`save-iteration ${saveRes.status}`);

      await loadIaSavedOutputs(currentToken);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "error";
      setIaError(`No se pudo guardar iteracion: ${msg}`);
    }
  }

  async function updateStage(stage: StageItem, status: string, progressPercent: number) {
    const currentToken = token.trim();
    if (!currentToken) return;
    setStagesError("");
    try {
      const res = await fetch(apiUrl(`/projects/${stage.project_id}/stages/${stage.stage_code}`), {
        method: "PUT",
        headers: buildAuthHeaders(currentToken),
        body: JSON.stringify({
          stage_status: status,
          progress_percent: progressPercent,
        }),
      });
      if (!res.ok) throw new Error(`update-stage ${res.status}`);
      await loadStages(String(stage.project_id));
      await loadData();
    } catch (err) {
      const message = err instanceof Error ? err.message : "error";
      setStagesError(message);
    }
  }

  async function logout() {
    const currentToken = token.trim();
    if (currentToken) {
      try {
        await fetch(apiUrl("/auth/logout"), {
          method: "POST",
          headers: {
            Authorization: `Bearer ${currentToken}`,
            "Content-Type": "application/json",
          },
        });
      } catch {
        // best effort logout
      }
    }

    sessionStorage.removeItem(SESSION_TOKEN_KEY);
    setToken("");
    setContext(null);
    setDashboard(null);
    setCosts(null);
    setProjectsData([]);
    setAgentsData([]);
    setAssignments([]);
    setRunsData([]);
    setStagesData([]);
    setError("");
    setAuthError("");
    setProjectError("");
    setAgentsError("");
    setRunsError("");
    setStagesError("");
    setAssignmentError("");
    setExecProjectId("");
    setExecAgentId("");
    setExecProvider("auto");
    setExecModel("");
    setExecPrompt("");
    setExecSystemPrompt("");
    setExecError("");
    setExecResult(null);
    setImgProjectId("");
    setImgAgentId("");
    setImgProvider("auto");
    setImgModel("");
    setImgSize("1024x1024");
    setImgPrompt("");
    setImgError("");
    setImgResult(null);
    setIaProjectId("");
    setIaAgentId("");
    setIaProvider("auto");
    setIaModel("");
    setIaSystemPrompt("");
    setIaPrompt("");
    setIaMessages([]);
    setIaConversationId(null);
    setIaSavedOutputs([]);
    setIaError("");
    setActiveTab("overview");
    setApiStatus("unknown");
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
          <button className={activeTab === "ia_generator" ? "active" : ""} onClick={() => setActiveTab("ia_generator")}>
            Generador IA
          </button>
        </nav>

        <div className="sidebar-footer">
          {context?.profile ? (
            <>
              <p>{context.profile.email ?? "Sin email"}</p>
              <button className="ghost" onClick={() => void logout()}>
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
            <span
              className={`status-dot ${
                loading ? "is-loading" : apiStatus === "online" ? "is-ready" : apiStatus === "offline" ? "is-offline" : ""
              }`}
            >
              {loading ? "Sincronizando" : apiStatus === "online" ? "Online" : apiStatus === "offline" ? "Offline" : "Estado"}
            </span>
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
            <article className="panel">
              <h4>Crear proyecto</h4>
              <div className="stack">
                <input
                  placeholder="Project key (ej: MKT-AI-001)"
                  value={newProjectKey}
                  onChange={(e) => setNewProjectKey(e.target.value.toUpperCase())}
                />
                <input
                  placeholder="Nombre del proyecto"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                />
                <select value={newProjectStatus} onChange={(e) => setNewProjectStatus(e.target.value)}>
                  <option value="draft">draft</option>
                  <option value="active">active</option>
                  <option value="paused">paused</option>
                  <option value="completed">completed</option>
                  <option value="cancelled">cancelled</option>
                </select>
                <button onClick={() => void createProject()} disabled={projectsLoading}>
                  Crear proyecto
                </button>
                <button className="ghost" onClick={() => void loadProjects()} disabled={projectsLoading}>
                  {projectsLoading ? "Cargando..." : "Refrescar listado"}
                </button>
              </div>
              {projectError ? <p className="error">{projectError}</p> : null}
            </article>
            <article className="panel">
              <h4>Proyectos</h4>
              {projectsData.length ? (
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Key</th>
                      <th>Nombre</th>
                      <th>Estado</th>
                      <th>Actualizado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projectsData.map((project) => (
                      <tr key={project.project_id}>
                        <td>{project.project_id}</td>
                        <td>{project.project_key}</td>
                        <td>{project.project_name}</td>
                        <td>{project.lifecycle_status}</td>
                        <td>{formatDate(project.updated_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="subtle">Sin proyectos cargados.</p>
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
              <button className="ghost compact" onClick={() => void loadRuns()} disabled={runsLoading}>
                {runsLoading ? "Cargando runs..." : "Cargar ultimas ejecuciones"}
              </button>
            </article>
            <article className="panel">
              <h4>Resumen economico</h4>
              <p className="total">
                Total 30d: <b>{formatCurrency(costs?.total_cost_usd ?? 0)}</b>
              </p>
              <p className="subtle">Runs: {costs?.total_runs_count ?? 0}</p>
              {runsError ? <p className="error">{runsError}</p> : null}
              {runsData.length ? (
                <table>
                  <thead>
                    <tr>
                      <th>Run ID</th>
                      <th>Project</th>
                      <th>Agent</th>
                      <th>Estado</th>
                      <th>Costo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runsData.slice(0, 8).map((run) => (
                      <tr key={run.agent_run_id}>
                        <td>{run.agent_run_id}</td>
                        <td>{run.project_id}</td>
                        <td>{run.agent_id}</td>
                        <td>{run.run_status}</td>
                        <td>{formatCurrency(run.cost_usd ?? 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
            </article>
          </section>
        ) : null}

        {activeTab === "ideas" ? (
          <section className="cards-2">
            <article className="panel">
              <h4>Project Stages (ideas por etapa)</h4>
              <p className="subtle">Carga y actualiza el avance real de etapas por proyecto.</p>
              <select value={stageProjectId} onChange={(e) => setStageProjectId(e.target.value)}>
                <option value="">Selecciona un proyecto</option>
                {projectsData.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.project_key} - {project.project_name}
                  </option>
                ))}
              </select>
              <button onClick={() => void loadStages(stageProjectId)} disabled={stagesLoading || !stageProjectId}>
                {stagesLoading ? "Cargando..." : "Cargar etapas"}
              </button>
              {stagesError ? <p className="error">{stagesError}</p> : null}
            </article>
            <article className="panel">
              <h4>Etapas del proyecto</h4>
              {stagesData.length ? (
                <div className="stage-list">
                  {stagesData.map((stage) => (
                    <div key={stage.project_stage_status_id} className="stage-row">
                      <div>
                        <strong>
                          {stage.stage_order}. {stage.stage_name}
                        </strong>
                        <p className="subtle">
                          {stage.stage_code} - {stage.stage_status} - {Math.round(stage.progress_percent)}%
                        </p>
                      </div>
                      <div className="stage-actions">
                        <button onClick={() => void updateStage(stage, "in_progress", Math.max(stage.progress_percent, 20))}>
                          In progress
                        </button>
                        <button onClick={() => void updateStage(stage, "blocked", stage.progress_percent)}>Blocked</button>
                        <button onClick={() => void updateStage(stage, "done", 100)}>Done</button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="subtle">Sin etapas cargadas.</p>
              )}
            </article>
          </section>
        ) : null}

        {activeTab === "agents" ? (
          <section className="cards-2">
            <article className="panel">
              <h4>Catalogo de agentes</h4>
              <div className="stack">
                <input
                  placeholder="Agent code (ej: planner-core)"
                  value={newAgentCode}
                  onChange={(e) => setNewAgentCode(e.target.value)}
                />
                <input
                  placeholder="Nombre de agente"
                  value={newAgentName}
                  onChange={(e) => setNewAgentName(e.target.value)}
                />
                <input
                  placeholder="Modulo"
                  value={newAgentModule}
                  onChange={(e) => setNewAgentModule(e.target.value)}
                />
                <input
                  placeholder="Equipo owner"
                  value={newAgentTeam}
                  onChange={(e) => setNewAgentTeam(e.target.value)}
                />
                <input
                  placeholder="Modelo default"
                  value={newAgentModel}
                  onChange={(e) => setNewAgentModel(e.target.value)}
                />
                <button onClick={() => void createAgent()} disabled={agentsLoading}>
                  Crear agente
                </button>
                <button className="ghost" onClick={() => void loadAgents()} disabled={agentsLoading}>
                  {agentsLoading ? "Cargando..." : "Refrescar agentes"}
                </button>
              </div>
              {agentsError ? <p className="error">{agentsError}</p> : null}
            </article>
            <article className="panel">
              <h4>Asignar agente a proyecto</h4>
              <div className="inline-2">
                <input
                  placeholder="Project ID"
                  value={assignmentProjectId}
                  onChange={(e) => setAssignmentProjectId(e.target.value)}
                />
                <input
                  placeholder="Agent ID"
                  value={assignmentAgentId}
                  onChange={(e) => setAssignmentAgentId(e.target.value)}
                />
              </div>
              <button onClick={() => void assignAgentToProject()}>Asignar</button>
              {assignmentError ? <p className="error">{assignmentError}</p> : null}

              <h4>Ejecutar agente (IA real)</h4>
              <div className="stack">
                <div className="inline-2">
                  <select value={execProjectId} onChange={(e) => setExecProjectId(e.target.value)}>
                    <option value="">Project ID</option>
                    {projectsData.map((project) => (
                      <option key={project.project_id} value={project.project_id}>
                        {project.project_id} - {project.project_key}
                      </option>
                    ))}
                  </select>
                  <select value={execAgentId} onChange={(e) => setExecAgentId(e.target.value)}>
                    <option value="">Agent ID</option>
                    {agentsData.map((agent) => (
                      <option key={agent.agent_id} value={agent.agent_id}>
                        {agent.agent_id} - {agent.agent_code}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="inline-2">
                  <select value={execProvider} onChange={(e) => setExecProvider(e.target.value)}>
                    <option value="auto">auto</option>
                    <option value="openai">openai</option>
                    <option value="gemini">gemini</option>
                  </select>
                  <input
                    placeholder="Model override (opcional)"
                    value={execModel}
                    onChange={(e) => setExecModel(e.target.value)}
                  />
                </div>
                <textarea
                  rows={3}
                  placeholder="System prompt (opcional)"
                  value={execSystemPrompt}
                  onChange={(e) => setExecSystemPrompt(e.target.value)}
                />
                <textarea
                  rows={5}
                  placeholder="Prompt de negocio para ejecutar el agente"
                  value={execPrompt}
                  onChange={(e) => setExecPrompt(e.target.value)}
                />
                <button
                  onClick={() => void executeAgentText()}
                  disabled={execLoading || !execProjectId || !execAgentId || !execPrompt.trim()}
                >
                  {execLoading ? "Ejecutando..." : "Ejecutar agente"}
                </button>
              </div>
              {execError ? <p className="error">{execError}</p> : null}
              {execResult ? (
                <div className="execution-result">
                  <p>
                    <strong>Run:</strong> {execResult.run_id} | <strong>Provider:</strong> {execResult.provider} |{" "}
                    <strong>Model:</strong> {execResult.model_name}
                  </p>
                  <p>
                    <strong>Tokens:</strong> in {execResult.token_input_count ?? 0} / out {execResult.token_output_count ?? 0} |{" "}
                    <strong>Costo:</strong> {formatCurrency(execResult.cost_usd ?? 0)}
                  </p>
                  <pre>{execResult.text || "(sin texto)"}</pre>
                </div>
              ) : null}

              <h4>Generar imagen (IA real)</h4>
              <div className="stack">
                <div className="inline-2">
                  <select value={imgProjectId} onChange={(e) => setImgProjectId(e.target.value)}>
                    <option value="">Project ID</option>
                    {projectsData.map((project) => (
                      <option key={project.project_id} value={project.project_id}>
                        {project.project_id} - {project.project_key}
                      </option>
                    ))}
                  </select>
                  <select value={imgAgentId} onChange={(e) => setImgAgentId(e.target.value)}>
                    <option value="">Agent ID</option>
                    {agentsData.map((agent) => (
                      <option key={agent.agent_id} value={agent.agent_id}>
                        {agent.agent_id} - {agent.agent_code}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="inline-2">
                  <select value={imgProvider} onChange={(e) => setImgProvider(e.target.value)}>
                    <option value="auto">auto</option>
                    <option value="openai">openai</option>
                    <option value="gemini">gemini</option>
                  </select>
                  <input placeholder="Model override (opcional)" value={imgModel} onChange={(e) => setImgModel(e.target.value)} />
                </div>
                <div className="inline-2">
                  <input placeholder="Size (1024x1024)" value={imgSize} onChange={(e) => setImgSize(e.target.value)} />
                  <span className="subtle">Se registra costo y run automaticamente</span>
                </div>
                <textarea
                  rows={4}
                  placeholder="Prompt de imagen"
                  value={imgPrompt}
                  onChange={(e) => setImgPrompt(e.target.value)}
                />
                <button onClick={() => void executeAgentImage()} disabled={imgLoading || !imgProjectId || !imgAgentId || !imgPrompt.trim()}>
                  {imgLoading ? "Generando..." : "Generar imagen"}
                </button>
              </div>
              {imgError ? <p className="error">{imgError}</p> : null}
              {imgResult ? (
                <div className="execution-result">
                  <p>
                    <strong>Run:</strong> {imgResult.run_id} | <strong>Provider:</strong> {imgResult.provider} |{" "}
                    <strong>Model:</strong> {imgResult.model_name} | <strong>Costo:</strong> {formatCurrency(imgResult.cost_usd ?? 0)}
                  </p>
                  {imgResult.image_url ? (
                    <img className="generated-image" src={imgResult.image_url} alt="Generated output" />
                  ) : null}
                  {!imgResult.image_url && imgResult.image_base64 ? (
                    <img
                      className="generated-image"
                      src={`data:${imgResult.mime_type ?? "image/png"};base64,${imgResult.image_base64}`}
                      alt="Generated output"
                    />
                  ) : null}
                </div>
              ) : null}

              {agentsData.length ? (
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Code</th>
                      <th>Nombre</th>
                      <th>Modulo</th>
                      <th>Activo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agentsData.map((agent) => (
                      <tr key={agent.agent_id}>
                        <td>{agent.agent_id}</td>
                        <td>{agent.agent_code}</td>
                        <td>{agent.agent_name}</td>
                        <td>{agent.module_name}</td>
                        <td>{agent.is_active ? "si" : "no"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
              {assignments.length ? (
                <>
                  <h4>Asignaciones activas</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Project</th>
                        <th>Agent</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {assignments.slice(0, 10).map((asn) => (
                        <tr key={asn.project_agent_assignment_id}>
                          <td>{asn.project_agent_assignment_id}</td>
                          <td>{asn.project_id}</td>
                          <td>{asn.agent_id}</td>
                          <td>{asn.assignment_status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : null}
            </article>
          </section>
        ) : null}

        {activeTab === "ia_generator" ? (
          <section className="cards-2">
            <article className="panel">
              <h4>Generador IA - Text IA</h4>
              <p className="subtle">Selecciona motor, contexto de proyecto/agente y ejecuta iteraciones de texto.</p>
              <div className="stack">
                <div className="inline-2">
                  <select value={iaProjectId} onChange={(e) => setIaProjectId(e.target.value)}>
                    <option value="">Project ID</option>
                    {projectsData.map((project) => (
                      <option key={project.project_id} value={project.project_id}>
                        {project.project_id} - {project.project_key}
                      </option>
                    ))}
                  </select>
                  <select value={iaAgentId} onChange={(e) => setIaAgentId(e.target.value)}>
                    <option value="">Agente especializado</option>
                    {agentsData.map((agent) => (
                      <option key={agent.agent_id} value={agent.agent_id}>
                        {agent.agent_id} - {agent.agent_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="inline-2">
                  <select value={iaProvider} onChange={(e) => setIaProvider(e.target.value)}>
                    <option value="auto">auto (fallback OpenAI a Gemini)</option>
                    <option value="openai">openai</option>
                    <option value="gemini">gemini</option>
                  </select>
                  <select value={iaModel} onChange={(e) => setIaModel(e.target.value)}>
                    <option value="">modelo por defecto</option>
                    <option value="gpt-5.2">gpt-5.2</option>
                    <option value="gemini-3-pro-preview">gemini-3-pro-preview</option>
                  </select>
                </div>

                <textarea
                  rows={3}
                  placeholder="System prompt (opcional)"
                  value={iaSystemPrompt}
                  onChange={(e) => setIaSystemPrompt(e.target.value)}
                />
                <textarea
                  rows={4}
                  placeholder="Escribe tu mensaje para iterar con el modelo"
                  value={iaPrompt}
                  onChange={(e) => setIaPrompt(e.target.value)}
                />
                <div className="inline-2">
                  <button onClick={() => void runTextIaIteration()} disabled={iaLoading || !iaProjectId || !iaAgentId || !iaPrompt.trim()}>
                    {iaLoading ? "Generando..." : "Enviar a Text IA"}
                  </button>
                  <button
                    className="ghost"
                    onClick={() => {
                      setIaMessages([]);
                      setIaError("");
                    }}
                  >
                    Nueva iteracion
                  </button>
                </div>
              </div>
              {iaError ? <p className="error">{iaError}</p> : null}
            </article>

            <article className="panel">
              <h4>Conversacion</h4>
              {iaMessages.length ? (
                <div className="chat-list">
                  {iaMessages.map((msg, idx) => (
                    <div key={`${msg.role}-${idx}`} className={`chat-bubble ${msg.role === "assistant" ? "assistant" : "user"}`}>
                      <p className="chat-role">{msg.role === "assistant" ? "Asistente IA" : "Tu"}</p>
                      <p>{msg.content}</p>
                      {msg.role === "assistant" && msg.runId ? (
                        <>
                          <small>
                            run {msg.runId} | {msg.provider} | {msg.model} | {formatCurrency(msg.costUsd ?? 0)}
                          </small>
                          <button className="ghost mini" onClick={() => void saveIaIteration(idx)}>
                            Guardar iteracion
                          </button>
                        </>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="subtle">Sin mensajes aun. Envia el primer prompt.</p>
              )}

              <h4>Iteraciones guardadas</h4>
              {iaSavedLoading ? <p className="subtle">Cargando guardados...</p> : null}
              {!iaSavedLoading && !iaSavedOutputs.length ? (
                <p className="subtle">No hay iteraciones guardadas para el filtro actual.</p>
              ) : null}
              {iaSavedOutputs.length ? (
                <div className="saved-iterations">
                  {iaSavedOutputs.map((it) => (
                    <div key={it.saved_output_id} className="saved-card">
                      <p className="saved-title">{it.label}</p>
                      <p className="subtle">
                        run {it.run_id ?? "-"} | {it.provider ?? "-"} | {it.model_name ?? "-"}
                      </p>
                      <p className="saved-content">{it.content}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </article>
          </section>
        ) : null}
      </main>
    </div>
  );
}

export default App;
