import QuestionnaireChatPanel from "../components/QuestionnaireChatPanel";
import { EmptyState } from "../components/UiBlocks";

export default function QuestionnairePage({ workflow }) {
  const { state, actions } = workflow;
  const answeredCount = state.chatMessages.filter((m) => m.role === "user").length;

  return (
    <div>
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
      />
      {!state.sessionId && (
        <EmptyState
          glyph="*"
          title="Start the Business Interview"
          description="Create a chat session to begin with: Tell me about your business."
        />
      )}
      {state.sessionId && state.chatMessages.length === 0 && (
        <EmptyState
          glyph="..."
          title="No Chat Messages Yet"
          description="Refresh or restart the session to load your first chatbot question."
        />
      )}
      {state.sessionId && answeredCount === 0 && (
        <EmptyState
          glyph=">"
          title="Waiting for Your First Answer"
          description="Once you answer, the chatbot will generate the next question automatically."
        />
      )}
      {state.interviewCompleted && (
        <EmptyState
          glyph="OK"
          title="Interview Completed"
          description="Go to Analysis page and run segment attractiveness analysis."
        />
      )}
    </div>
  );
}
