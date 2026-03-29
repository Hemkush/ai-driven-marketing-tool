import { useEffect, useMemo, useState } from "react";
import { setAuthToken } from "../lib/api";
import {
  authClient,
  contentClient,
  pipelineClient,
  projectClient,
  questionnaireClient,
} from "../lib/mvpClient";

export function useMvpWorkflow() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [me, setMe] = useState(null);
  const [msg, setMsg] = useState("");
  const [toasts, setToasts] = useState([]);
  const [busy, setBusy] = useState(false);

  const [projects, setProjects] = useState([]);
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [projectBusinessAddress, setProjectBusinessAddress] = useState("");
  const [activeProjectId, setActiveProjectId] = useState("");

  const [sessionId, setSessionId] = useState(null);
  const [projectSessions, setProjectSessions] = useState([]);
  const [selectedProjectSessionId, setSelectedProjectSessionId] = useState("");
  const [selectedProjectSessionDetail, setSelectedProjectSessionDetail] = useState(null);
  const [selectedProjectSessionWorkflow, setSelectedProjectSessionWorkflow] = useState(null);
  const [responses, setResponses] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [interviewStatus, setInterviewStatus] = useState("idle");
  const [interviewCoverage, setInterviewCoverage] = useState(null);
  const [interviewAnalysis, setInterviewAnalysis] = useState(null);

  const [analysis, setAnalysis] = useState(null);
  const [analysisAssistantMessages, setAnalysisAssistantMessages] = useState([]);
  const [analysisAssistantInput, setAnalysisAssistantInput] = useState("");
  const [analysisAssistantBusy, setAnalysisAssistantBusy] = useState(false);
  const [positioning, setPositioning] = useState(null);
  const [positioningHistory, setPositioningHistory] = useState([]);
  const [positioningFeedback, setPositioningFeedback] = useState("");
  const [research, setResearch] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [strategy, setStrategy] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [contentAssets, setContentAssets] = useState([]);
  const [assetType, setAssetType] = useState("social_post");
  const [assetPrompt, setAssetPrompt] = useState("Create premium launch-week content.");
  const [numVariants, setNumVariants] = useState(3);

  const activeProject = useMemo(
    () => projects.find((p) => String(p.id) === String(activeProjectId)) || null,
    [projects, activeProjectId]
  );

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    setAuthToken(token);
    Promise.all([authClient.me(), projectClient.list()])
      .then(([meData, items]) => {
        setMe(meData);
        setProjects(items);
        if (items.length > 0) setActiveProjectId(String(items[0].id));
      })
      .catch(() => {
        setAuthToken(null);
      });
  }, []);

  useEffect(() => {
    if (!activeProjectId) {
      setProjectSessions([]);
      setSelectedProjectSessionId("");
      setSelectedProjectSessionDetail(null);
      setSelectedProjectSessionWorkflow(null);
      return;
    }
    actions.loadProjectSessions(String(activeProjectId));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeProjectId]);

  useEffect(() => {
    if (!msg || msg.endsWith("...")) return;
    const toast = {
      id: `${Date.now()}-${Math.random()}`,
      message: msg,
      type: /failed|error|cannot|not found|required/i.test(msg) ? "error" : "success",
    };
    setToasts((prev) => [toast, ...prev].slice(0, 4));
  }, [msg]);

  const run = async (fn, loadingMsg = "Working...") => {
    setBusy(true);
    setMsg(loadingMsg);
    try {
      const result = await fn();
      return { ok: true, result };
    } catch (e) {
      setMsg(e?.response?.data?.detail || e?.message || "Request failed");
      return { ok: false, result: null };
    } finally {
      setBusy(false);
    }
  };

  const refreshSelectedSessionWorkflow = async (sessionIdOverride = "") => {
    const normalized = String(sessionIdOverride || selectedProjectSessionId || "");
    if (!normalized) return;
    const workflowSummary = await questionnaireClient.getSessionWorkflowSummary(
      Number(normalized)
    );
    setSelectedProjectSessionWorkflow(workflowSummary);
  };

  // Unpack a session workflow snapshot into individual state variables.
  // Called after loadProjectSessions / selectProjectSession so every page
  // sees correct data immediately after login or session switch.
  const _applySnapshot = (snap) => {
    setAnalysis(snap?.analysis?.report ?? null);
    setResearch(snap?.research?.report ?? null);
    setPersonas(snap?.personas ?? []);
    setStrategy(snap?.strategy?.strategy ?? null);
    setRoadmap(snap?.roadmap?.roadmap ?? null);
    const pos = snap?.positioning ?? null;
    setPositioning(pos);
    setPositioningHistory(pos ? [pos] : []);
    setContentAssets(snap?.content_assets ?? []);
  };

  const actions = {
    register: async () =>
      run(async () => {
        if (!companyName.trim()) {
          throw new Error("Company/organization name is required");
        }
        await authClient.register({
          email,
          password,
          full_name: companyName.trim(),
        });
        setMsg("Registered. Login now.");
      }, "Registering..."),

    login: async () =>
      run(async () => {
        const auth = await authClient.login({ email, password });
        setAuthToken(auth.access_token);
        const [meData, items] = await Promise.all([authClient.me(), projectClient.list()]);
        setMe(meData);
        setProjects(items);
        setActiveProjectId(items.length ? String(items[0].id) : "");
        setMsg("Logged in.");
      }, "Logging in..."),

    logout: () => {
      setAuthToken(null);
      setMe(null);
      setProjects([]);
      setActiveProjectId("");
      setSessionId(null);
      setProjectSessions([]);
      setSelectedProjectSessionId("");
      setSelectedProjectSessionDetail(null);
      setSelectedProjectSessionWorkflow(null);
      setResponses([]);
      setChatMessages([]);
      setInterviewStatus("idle");
      setInterviewCoverage(null);
      setInterviewAnalysis(null);
      setAnalysis(null);
      setAnalysisAssistantMessages([]);
      setAnalysisAssistantInput("");
      setPositioning(null);
      setPositioningHistory([]);
      setResearch(null);
      setPersonas([]);
      setStrategy(null);
      setRoadmap(null);
      setContentAssets([]);
      setMsg("Logged out.");
    },

    dismissToast: (id) => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    },

    loadProjects: async () =>
      run(async () => {
        const items = await projectClient.list();
        setProjects(items);
        if (!activeProjectId && items.length) {
          setActiveProjectId(String(items[0].id));
        }
        setMsg("Business profiles refreshed.");
      }, "Loading business profiles..."),

    createProject: async () =>
      run(async () => {
        const data = await projectClient.create({
          name: projectName,
          description: projectDescription || null,
          business_address: projectBusinessAddress || null,
        });
        setProjects((prev) => [data, ...prev]);
        setActiveProjectId(String(data.id));
        setProjectName("");
        setProjectDescription("");
        setProjectBusinessAddress("");
        setMsg("Business profile created.");
      }, "Creating business profile..."),

    startQuestionnaireSession: async () =>
      run(async () => {
        if (!activeProjectId) throw new Error("Select business profile first");
        const data = await questionnaireClient.startSession(Number(activeProjectId));
        setSessionId(data.id);
        const session = await questionnaireClient.getSession(data.id);
        setResponses(session.responses || []);
        await actions.loadProjectSessions(String(activeProjectId), String(data.id));
        setMsg(`Questionnaire session started (#${data.id}) with default profile questions.`);
      }, "Starting session..."),

    startQuestionnaireChat: async () =>
      run(async () => {
        if (!activeProjectId) throw new Error("Select business profile first");
        const data = await questionnaireClient.chatStart(Number(activeProjectId));
        setSessionId(data.session_id);
        setChatMessages(data.messages || []);
        setInterviewStatus(data.status || "in_progress");
        setInterviewCoverage(null);
        setInterviewAnalysis(null);
        await actions.loadProjectSessions(String(activeProjectId), String(data.session_id));
        setMsg("Business interview chat started.");
      }, "Starting chatbot..."),

    loadQuestionnaireChat: async () =>
      run(async () => {
        if (!activeProjectId) throw new Error("Select business profile first");
        const data = await questionnaireClient.chatStart(Number(activeProjectId));
        setSessionId(data.session_id);
        setChatMessages([...(data.messages || [])]);
        setResponses([]);
        setInterviewStatus(data.status || "in_progress");
        setInterviewCoverage(null);
        setInterviewAnalysis(null);
        setMsg("Conversation restarted with a new interview session.");
      }, "Refreshing conversation..."),

    sendQuestionnaireChatReply: async (answerText) =>
      run(async () => {
        if (!sessionId) throw new Error("Start chat first");
        const text = (answerText || "").trim();
        if (!text) throw new Error("Enter an answer first");

        const data = await questionnaireClient.chatReply(sessionId, text);
        const userMessage = {
          role: "user",
          response_id: data.saved_response.id,
          sequence_no: data.saved_response.sequence_no,
          answer_text: data.saved_response.answer_text,
        };
        const botMessage = {
          role: "assistant",
          response_id: data.next_question.id,
          sequence_no: data.next_question.sequence_no,
          question_text: data.next_question.question_text,
          question_type: data.next_question.question_type,
          question_options: data.next_question.question_options || [],
          source: data.next_question.source,
        };
        setChatMessages((prev) => [...prev, userMessage, botMessage]);
        setInterviewStatus(data.status || "in_progress");
        setInterviewCoverage(data.coverage || null);
        setInterviewAnalysis(data.analysis || null);
        setMsg("Answer saved. Next question ready.");
      }, "Analyzing your answer..."),

    finishQuestionnaireChat: async (force = false) =>
      run(async () => {
        if (!sessionId) throw new Error("Start chat first");
        const data = await questionnaireClient.chatFinish(sessionId, force);
        setInterviewStatus(data.status || "completed");
        setInterviewCoverage(data.coverage || null);
        await refreshSelectedSessionWorkflow(String(sessionId));
        const missing = data.missing_topics || [];
        if (missing.length) {
          setMsg(`Interview finished. Missing topics: ${missing.join(", ")}`);
        } else {
          setMsg("Interview finished. Analysis is now enabled.");
        }
      }, "Finishing interview..."),

    loadQuestionnaireSession: async () =>
      run(async () => {
        if (!sessionId) throw new Error("Start session first");
        const data = await questionnaireClient.getSession(sessionId);
        setResponses(data.responses || []);
        setMsg("Session loaded.");
      }, "Loading session..."),

    loadProjectSessions: async (projectIdOverride = "", preferredSessionId = "") =>
      run(async () => {
        const projectId = Number(projectIdOverride || activeProjectId);
        if (!projectId) throw new Error("Select business profile first");
        const data = await questionnaireClient.listSessionsByBusinessProfile(projectId);
        const items = data.items || [];
        setProjectSessions(items);
        const nextSessionId = String(preferredSessionId || data.latest_session_id || items[0]?.id || "");
        setSelectedProjectSessionId(nextSessionId);
        if (nextSessionId) {
          const [detail, workflowSummary] = await Promise.all([
            questionnaireClient.getSession(Number(nextSessionId)),
            questionnaireClient.getSessionWorkflowSummary(Number(nextSessionId)),
          ]);
          setSelectedProjectSessionDetail(detail);
          setSelectedProjectSessionWorkflow(workflowSummary);
          if (detail?.status) setInterviewStatus(detail.status);
          _applySnapshot(workflowSummary?.snapshot);
          if (detail?.status && detail.status !== "idle") {
            try {
              const chatData = await questionnaireClient.chatGet(Number(nextSessionId));
              setSessionId(Number(nextSessionId));
              setChatMessages(chatData.messages || []);
              setInterviewAnalysis(chatData.analysis || null);
              setInterviewCoverage(chatData.coverage || null);
            } catch { /* no chat messages yet */ }
          }
        } else {
          setSelectedProjectSessionDetail(null);
          setSelectedProjectSessionWorkflow(null);
          setInterviewStatus("idle");
          _applySnapshot(null);
        }
      }, "Loading business profile sessions..."),

    selectProjectSession: async (nextSessionId) =>
      run(async () => {
        const normalized = String(nextSessionId || "");
        setSelectedProjectSessionId(normalized);
        if (!normalized) {
          setSelectedProjectSessionDetail(null);
          setSelectedProjectSessionWorkflow(null);
          _applySnapshot(null);
          return;
        }
        const [detail, workflowSummary] = await Promise.all([
          questionnaireClient.getSession(Number(normalized)),
          questionnaireClient.getSessionWorkflowSummary(Number(normalized)),
        ]);
        setSelectedProjectSessionDetail(detail);
        setSelectedProjectSessionWorkflow(workflowSummary);
        if (detail?.status) setInterviewStatus(detail.status);
        _applySnapshot(workflowSummary?.snapshot);
        if (detail?.status && detail.status !== "idle") {
          try {
            const chatData = await questionnaireClient.chatGet(Number(normalized));
            setSessionId(Number(normalized));
            setChatMessages(chatData.messages || []);
            setInterviewAnalysis(chatData.analysis || null);
            setInterviewCoverage(chatData.coverage || null);
          } catch { /* no chat messages yet */ }
        }
      }, "Loading session details..."),

    generateNextQuestions: async () =>
      run(async () => {
        if (!sessionId) throw new Error("Start session first");
        await questionnaireClient.generateNextQuestions(sessionId);
        await actions.loadQuestionnaireSession();
        setMsg("Suggested follow-up questions generated.");
      }, "Generating follow-up questions..."),

    acceptSuggested: async (responseId) =>
      run(async () => {
        await questionnaireClient.accept(responseId);
        await actions.loadQuestionnaireSession();
      }, "Accepting suggestion..."),

    rejectSuggested: async (responseId) =>
      run(async () => {
        await questionnaireClient.reject(responseId);
        await actions.loadQuestionnaireSession();
      }, "Rejecting suggestion..."),

    saveQuestionnaireAnswersBulk: async (entries) =>
      run(async () => {
        if (!entries || entries.length === 0) {
          throw new Error("No answers to save");
        }
        for (const item of entries) {
          if (!item.answerText?.trim()) continue;
          await questionnaireClient.answer(item.responseId, item.answerText.trim());
        }
        await actions.loadQuestionnaireSession();
        setMsg("Answers saved.");
      }, "Saving answers..."),

    runAnalysis: async () =>
      run(async () => {
        const assistantContext = analysisAssistantMessages
          .filter((m) => m.role === "user")
          .map((m) => m.content?.trim())
          .filter(Boolean)
          .slice(-6)
          .join("\n");
        const data = await pipelineClient.runAnalysis(
          Number(activeProjectId),
          assistantContext
        );
        setAnalysis(data.report);
        await refreshSelectedSessionWorkflow();
        setMsg(
          assistantContext
            ? "Analysis regenerated using discovery responses and assistant context."
            : "Analysis generated."
        );
      }, "Generating analysis..."),

    askAnalysisAssistant: async (overrideMessage = "") =>
      (async () => {
        setAnalysisAssistantBusy(true);
        setMsg("Consulting analysis assistant...");
        try {
          const message = (overrideMessage || analysisAssistantInput).trim();
          if (!message) throw new Error("Enter an analysis question first");
          if (!activeProjectId) throw new Error("Select business profile first");
          if (!analysis) throw new Error("Run analysis first");

          const userMessage = { role: "user", content: message };
          const history = [...analysisAssistantMessages, userMessage]
            .slice(-12)
            .map((x) => ({ role: x.role, content: x.content }));

          // Show user message immediately, then render assistant typing state.
          setAnalysisAssistantMessages((prev) => [...prev, userMessage]);
          setAnalysisAssistantInput("");

          const data = await pipelineClient.queryAnalysisAssistant(
            Number(activeProjectId),
            message,
            history
          );
          const assistantText = data.answer || "No answer generated.";
          const suffix = data.recommend_rerun
            ? `\n\nRecommendation: Rerun analysis. ${data.rerun_reason || ""}`.trim()
            : "";
          const assistantMessage = {
            role: "assistant",
            content: `${assistantText}${suffix}`,
            source: data.source || "fallback",
          };
          setAnalysisAssistantMessages((prev) => [...prev, assistantMessage]);
          setMsg("Analysis assistant responded.");
          return { ok: true, result: data };
        } catch (e) {
          const errText = e?.response?.data?.detail || e?.message || "Request failed";
          setAnalysisAssistantMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `I couldn't complete that request.\n\nSummary:\n- ${errText}`,
              source: "fallback",
            },
          ]);
          setMsg(errText);
          return { ok: false, result: null };
        } finally {
          setAnalysisAssistantBusy(false);
        }
      })(),

    generatePositioning: async () =>
      run(async () => {
        const data = await pipelineClient.generatePositioning(Number(activeProjectId));
        setPositioning(data.positioning);
        setPositioningHistory((prev) => [data.positioning, ...prev]);
        await refreshSelectedSessionWorkflow();
        setMsg("Positioning generated.");
      }, "Generating positioning..."),

    refinePositioning: async () =>
      run(async () => {
        if (!positioningFeedback.trim()) throw new Error("Enter feedback first");
        const data = await pipelineClient.refinePositioning(
          Number(activeProjectId),
          positioningFeedback
        );
        setPositioning(data.positioning);
        setPositioningHistory((prev) => [data.positioning, ...prev]);
        setPositioningFeedback("");
        await refreshSelectedSessionWorkflow();
        setMsg("Positioning refined.");
      }, "Refining positioning..."),

    loadPositioningHistory: async (sessionIdOverride) =>
      run(async () => {
        if (!activeProjectId) throw new Error("Select business profile first");
        const sid = sessionIdOverride || selectedProjectSessionId || null;
        const items = await pipelineClient.listPositioning(Number(activeProjectId), sid ? Number(sid) : null);
        setPositioningHistory(items);
        setPositioning(items[0] || null);
      }, "Loading positioning history..."),

    runResearch: async () =>
      run(async () => {
        const data = await pipelineClient.runResearch(Number(activeProjectId));
        setResearch(data.report);
        await refreshSelectedSessionWorkflow();
        setMsg("Research generated.");
      }, "Generating research..."),

    generatePersonas: async () =>
      run(async () => {
        const data = await pipelineClient.generatePersonas(Number(activeProjectId));
        setPersonas(data.personas || []);
        await refreshSelectedSessionWorkflow();
        setMsg("Personas generated.");
      }, "Generating personas..."),

    generateStrategy: async () =>
      run(async () => {
        const data = await pipelineClient.generateStrategy(Number(activeProjectId));
        setStrategy(data.strategy);
        await refreshSelectedSessionWorkflow();
        setMsg("Channel strategy generated.");
      }, "Generating strategy..."),

    generateRoadmap: async () =>
      run(async () => {
        const data = await pipelineClient.generateRoadmap(Number(activeProjectId));
        setRoadmap(data.roadmap);
        await refreshSelectedSessionWorkflow();
        setMsg("Roadmap generated.");
      }, "Generating roadmap..."),

    generateContent: async () =>
      run(async () => {
        const data = await contentClient.generate({
          business_profile_id: Number(activeProjectId),
          asset_type: assetType,
          prompt_text: assetPrompt,
          num_variants: Number(numVariants),
        });
        setContentAssets(data.assets || []);
        await refreshSelectedSessionWorkflow();
        setMsg("Content assets generated.");
      }, "Generating content assets..."),

    loadContentAssets: async () =>
      run(async () => {
        const items = await contentClient.listByProject(activeProjectId);
        setContentAssets(items);
        setMsg("Loaded stored assets.");
      }, "Loading content assets..."),
  };

  return {
    state: {
      email,
      password,
      companyName,
      me,
      msg,
      toasts,
      busy,
      projects,
      projectName,
      projectDescription,
      projectBusinessAddress,
      activeProjectId,
      activeProject,
      sessionId,
      projectSessions,
      selectedProjectSessionId,
      selectedProjectSessionDetail,
      selectedProjectSessionWorkflow,
      responses,
      chatMessages,
      interviewStatus,
      interviewCoverage,
      interviewAnalysis,
      interviewCompleted: interviewStatus === "completed",
      analysis,
      analysisAssistantBusy,
      analysisAssistantMessages,
      analysisAssistantInput,
      positioning,
      positioningHistory,
      positioningFeedback,
      research,
      personas,
      strategy,
      roadmap,
      contentAssets,
      assetType,
      assetPrompt,
      numVariants,
    },
    set: {
      setEmail,
      setPassword,
      setCompanyName,
      setProjectName,
      setProjectDescription,
      setProjectBusinessAddress,
      setActiveProjectId,
      setSelectedProjectSessionId,
      setPositioningFeedback,
      setAssetType,
      setAssetPrompt,
      setNumVariants,
      setAnalysisAssistantInput,
    },
    actions,
  };
}
