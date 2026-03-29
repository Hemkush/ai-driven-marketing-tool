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
      {state.sessionId && (
        <NextStepCta to="/analysis" label="Next: Competitive Benchmarking" disabled={!state.interviewCompleted} />
      )}
    </div>
  );
}
