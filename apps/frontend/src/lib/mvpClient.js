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
  runResearch: (businessProfileId) =>
    api.post("/mvp/research/run", { business_profile_id: businessProfileId }).then((r) => r.data),
  generatePersonas: (businessProfileId) =>
    api
      .post("/mvp/personas/generate", { business_profile_id: businessProfileId })
      .then((r) => r.data),
  generateStrategy: (businessProfileId) =>
    api
      .post("/mvp/strategy/generate", { business_profile_id: businessProfileId })
      .then((r) => r.data),
  generateRoadmap: (businessProfileId) =>
    api
      .post("/mvp/roadmap/generate", { business_profile_id: businessProfileId })
      .then((r) => r.data),
};

export const contentClient = {
  generate: (payload) => api.post("/mvp/content/generate", payload).then((r) => r.data),
  listByProject: (businessProfileId) =>
    api.get(`/mvp/content/assets/${businessProfileId}`).then((r) => r.data.items || []),
};
