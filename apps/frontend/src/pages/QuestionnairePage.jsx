import QuestionnaireChatPanel from "../components/QuestionnaireChatPanel";
import { NextStepCta } from "../components/UiBlocks";

export default function QuestionnairePage({ workflow }) {
  const { state, actions } = workflow;

  return (
    <div className="qp-page">
      <QuestionnaireChatPanel
        startChat={actions.startQuestionnaireChat}
        refreshChat={actions.loadQuestionnaireChat}
        sendReply={actions.sendQuestionnaireChatReply}
        finishChat={actions.finishQuestionnaireChat}
        busy={state.busy}
        activeProjectId={state.activeProjectId}
        sessionId={state.sessionId}
        messages={state.chatMessages}
        analysis={state.interviewAnalysis}
        interviewCompleted={state.interviewCompleted}
      />
      <p style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "16px", lineHeight: 1.5 }}>
        Your answers are used only to generate your personalised marketing strategy. No data is sold or shared with third parties.
        AI-generated outputs are for guidance only — review before acting.
      </p>
      {state.sessionId && (
        <NextStepCta to="/analysis" label="Next: Competitive Benchmarking" disabled={!state.interviewCompleted} />
      )}
    </div>
  );
}
