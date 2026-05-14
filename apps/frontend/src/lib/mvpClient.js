import { api } from "./api";

export const authClient = {
  register: (payload) => api.post("/auth/register", payload).then((r) => r.data),
  login: (payload) => api.post("/auth/login", payload).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
  resendVerification: (email) =>
    api.post("/auth/resend-verification", { email }).then((r) => r.data),
  verifyEmail: (token) => api.get(`/auth/verify-email?token=${token}`).then((r) => r.data),
};

export const projectClient = {
  list: () => api.get("/business-profiles").then((r) => r.data.items || []),
  create: (payload) => api.post("/business-profiles", payload).then((r) => r.data),
};

export const questionnaireClient = {
  startSession: (businessProfileId) =>
    api
      .post("/mvp/questionnaire/sessions", { business_profile_id: businessProfileId })
      .then((r) => r.data),
  getSession: (sessionId) =>
    api.get(`/mvp/questionnaire/sessions/${sessionId}`).then((r) => r.data),
  getSessionWorkflowSummary: (sessionId) =>
    api.get(`/mvp/workflow/session-summary/${sessionId}`).then((r) => r.data),
  listSessionsByBusinessProfile: (businessProfileId) =>
    api.get(`/mvp/questionnaire/sessions/by-business-profile/${businessProfileId}`).then((r) => r.data),
  addResponse: (sessionId, payload) =>
    api.post(`/mvp/questionnaire/sessions/${sessionId}/responses`, payload).then((r) => r.data),
  generateNextQuestions: (sessionId) =>
    api.post(`/mvp/questionnaire/sessions/${sessionId}/next-questions`).then((r) => r.data),
  accept: (responseId) =>
    api.post(`/mvp/questionnaire/responses/${responseId}/accept`).then((r) => r.data),
  reject: (responseId) =>
    api.post(`/mvp/questionnaire/responses/${responseId}/reject`).then((r) => r.data),
  answer: (responseId, answerText) =>
    api
      .patch(`/mvp/questionnaire/responses/${responseId}`, { answer_text: answerText })
      .then((r) => r.data),
  chatStart: (businessProfileId) =>
    api
      .post("/mvp/questionnaire/chat/start", { business_profile_id: businessProfileId })
      .then((r) => r.data),
  chatGet: (sessionId) =>
    api
      .get(`/mvp/questionnaire/chat/${sessionId}`, {
        params: { _ts: Date.now() },
      })
      .then((r) => r.data),
  chatReply: (sessionId, answerText) =>
    api
      .post(`/mvp/questionnaire/chat/${sessionId}/reply`, { answer_text: answerText })
      .then((r) => r.data),
  chatFinish: (sessionId, force = false) =>
    api
      .post(`/mvp/questionnaire/chat/${sessionId}/finish`, { force })
      .then((r) => r.data),
};

export const pipelineClient = {
  runAnalysis: (businessProfileId, additionalContext = "") =>
    api
      .post("/mvp/analysis/run", {
        business_profile_id: businessProfileId,
        additional_context: additionalContext || null,
      })
      .then((r) => r.data),
  queryAnalysisAssistant: (businessProfileId, message, history = []) =>
    api
      .post("/mvp/analysis/assistant/query", {
        business_profile_id: businessProfileId,
        message,
        history,
      })
      .then((r) => r.data),
  generatePositioning: (businessProfileId) =>
    api
      .post("/mvp/positioning/generate", { business_profile_id: businessProfileId })
      .then((r) => r.data),
  refinePositioning: (businessProfileId, ownerFeedback) =>
    api
      .post("/mvp/positioning/refine", {
        business_profile_id: businessProfileId,
        owner_feedback: ownerFeedback,
      })
      .then((r) => r.data),
  listPositioning: (businessProfileId, sessionId) => {
    const params = sessionId ? { session_id: sessionId } : {};
    return api.get(`/mvp/positioning/${businessProfileId}`, { params }).then((r) => r.data.items || []);
  },
  runResearch: (businessProfileId, focusArea) =>
    api
      .post("/mvp/research/run", {
        business_profile_id: businessProfileId,
        force_refresh: true,
        ...(focusArea ? { focus_area: focusArea } : {}),
      })
      .then((r) => r.data),
  generatePersonas: (businessProfileId, ownerFeedback) =>
    api
      .post("/mvp/personas/generate", {
        business_profile_id: businessProfileId,
        ...(ownerFeedback ? { owner_feedback: ownerFeedback } : {}),
      })
      .then((r) => r.data),
  generateRoadmap: (businessProfileId) =>
    api
      .post("/mvp/roadmap/generate", { business_profile_id: businessProfileId })
      .then((r) => r.data),

  runAnalysisStream: (businessProfileId, additionalContext, { onStep, onComplete, onError } = {}) => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
    const token = localStorage.getItem("access_token");
    return fetch(`${apiBase}/mvp/analysis/run/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        business_profile_id: businessProfileId,
        additional_context: additionalContext || null,
      }),
    }).then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const chunk of parts) {
          for (const line of chunk.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === "step") onStep?.(event);
              else if (event.type === "complete") onComplete?.(event);
              else if (event.type === "error") onError?.(new Error(event.message));
            } catch { /* ignore malformed lines */ }
          }
        }
      }
    });
  },
};

export const contentClient = {
  generate: (payload) => api.post("/mvp/content/generate", payload).then((r) => r.data),

  generateStream: (payload, { onStep, onComplete, onError } = {}) => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
    const token = localStorage.getItem("access_token");
    return fetch(`${apiBase}/mvp/content/generate/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    }).then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const chunk of parts) {
          for (const line of chunk.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === "step") onStep?.(event);
              else if (event.type === "complete") onComplete?.(event);
              else if (event.type === "error") onError?.(new Error(event.message));
            } catch { /* ignore malformed lines */ }
          }
        }
      }
    });
  },
  listByProject: (businessProfileId) =>
    api.get(`/mvp/content/assets/${businessProfileId}`).then((r) => r.data.items || []),
  suggestTone: (businessProfileId) =>
    api.get(`/mvp/content/suggest-tone/${businessProfileId}`).then((r) => r.data),
};

export const submitFeedback = (payload) =>
  api.post("/mvp/feedback", payload).then((r) => r.data);
