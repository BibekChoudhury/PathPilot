import React, { useState } from 'react';
import { Bot, Send, User, Sparkles, Terminal, CheckCircle2, AlertCircle, RefreshCw, ArrowRight, Clock, BookOpen, PenTool } from 'lucide-react';
import { api, AgentRun, Plan } from '../api';

interface MentorChatProps {
  currentPlan: Plan | null;
  onPlanUpdated: () => void;
  onStartPractice: (skillId: string, assessmentId?: string) => void;
  onSelectTab?: (tab: string) => void;
  initialSkillId?: string;
}

interface MessageItem {
  id: string;
  sender: 'user' | 'mentor';
  text: string;
  actionRun?: AgentRun;
  timestamp: string;
}

export const MentorChat: React.FC<MentorChatProps> = ({
  currentPlan,
  onPlanUpdated,
  onStartPractice,
  onSelectTab,
  initialSkillId,
}) => {
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: 'msg-welcome',
      sender: 'mentor',
      text: (
        "Welcome to your Margin Notes & Physics Recovery Companion.\n\n" +
        "I provide step-by-step physical derivations, clarify misconceptions, and adjust your study timetable to your available time.\n\n" +
        "Try asking: “Explain vector components”, “I only have 30 minutes today”, or “What if I only had 30 minutes? (Preview)”."
      ),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState<string>(() =>
    initialSkillId
      ? 'Explain ' +
        ({
          vector_components: 'vector components',
          vector_addition: 'vector addition',
          constant_accel_1d: '1D motion with constant acceleration',
        } as Record<string, string>)[initialSkillId]
      : ''
  );
  const [loading, setLoading] = useState<boolean>(false);

  const samplePrompts = [
    "Explain vector components",
    "I only have 30 minutes today",
    "Start practice on vector addition",
    "What if I only had 30 minutes? (Preview)",
    "My JEE Main CRL rank is 1500, can I get NIT CS?",
  ];

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: MessageItem = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!messageText) setInput('');
    setLoading(true);

    try {
      const res = await api.runMentor(textToSend, currentPlan?.version);

      const mentorMsg: MessageItem = {
        id: `mnt-${Date.now()}`,
        sender: 'mentor',
        text: res.reply_text,
        actionRun: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, mentorMsg]);

      // If tool was replan, trigger parent plan refresh
      if (res.requested_action === 'replan') {
        onPlanUpdated();
      } else if (res.requested_action === 'start_practice' && res.tool_result?.skill_id) {
        onStartPractice(res.tool_result.skill_id, res.tool_result.assessment_id);
      }
    } catch (err: any) {
      const errMsg: MessageItem = {
        id: `err-${Date.now()}`,
        sender: 'mentor',
        text: `Error executing request: ${err.message || 'Network or server issue'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-textbook max-w-4xl mx-auto flex flex-col h-[680px] border-[#EDE3CE] bg-white shadow-textbook p-0 overflow-hidden animate-fade-in font-sans">
      {/* Header */}
      <div className="p-4 sm:p-5 border-b border-[#EDE3CE] bg-[#FAF6ED] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-white border border-[#DFD3B9] flex items-center justify-center text-[#D9381E] shadow-2xs">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-[#0A1C2E] font-serif">
                Margin Notes & Physics Mentor
              </h3>
              <span className="badge-vermilion text-[10px]">Textbook Notes</span>
            </div>
            <p className="text-xs text-[#627D98]">
              Annotated concept derivations, study assistance, and verified timetable adjustments
            </p>
          </div>
        </div>
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-4 py-2.5 bg-[#FFFFFF] border-b border-[#EDE3CE] overflow-x-auto flex items-center gap-2 scrollbar-none">
        <span className="text-[11px] font-mono uppercase text-[#D9381E] font-bold shrink-0 tracking-wider">
          Suggested:
        </span>
        {samplePrompts.map((p, idx) => (
          <button
            key={idx}
            disabled={loading}
            onClick={() => handleSend(p)}
            className="px-3 py-1 rounded bg-[#FAF6ED] hover:bg-[#F5EFE0] border border-[#EDE3CE] text-xs text-[#334E68] hover:text-[#0A1C2E] whitespace-nowrap transition-colors font-sans"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Chat Messages Body */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 bg-[#FBF7EE]/60">
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          const isPreview = m.text.toLowerCase().includes('preview') || m.text.toLowerCase().includes('what if');

          return (
            <div
              key={m.id}
              className={`flex items-start gap-3.5 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded shrink-0 flex items-center justify-center text-xs font-bold ${
                  isUser
                    ? 'bg-[#102A43] text-white shadow-2xs'
                    : 'bg-white border border-[#EDE3CE] text-[#D9381E] shadow-2xs'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <PenTool className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[85%] sm:max-w-[80%] rounded p-4 text-xs sm:text-sm leading-relaxed ${
                  isUser
                    ? 'bg-[#102A43] text-white shadow-xs'
                    : 'bg-white border border-[#EDE3CE] text-[#0A1C2E] shadow-2xs border-l-4 border-l-[#D9381E]'
                }`}
              >
                {/* Preview vs Saved Notice */}
                {isPreview && !isUser && (
                  <div className="mb-2.5 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-[#FFF9F2] border border-[#F6D6BA] text-[#7B341E] text-[10px] font-mono font-bold uppercase tracking-wider">
                    <span>Textbook Preview Only — Not Saved to Schedule</span>
                  </div>
                )}

                <div className={`whitespace-pre-wrap ${!isUser ? 'font-serif text-[15px] leading-relaxed' : 'font-sans'}`}>
                  {m.text}
                </div>

                {/* Plan Update Result Card */}
                {m.actionRun && m.actionRun.requested_action === 'replan' && m.actionRun.tool_result && (
                  <div className="mt-4 p-4 rounded bg-[#FAF6ED] border border-[#EDE3CE] text-xs font-sans">
                    <div className="flex items-center justify-between border-b border-[#EDE3CE] pb-2 mb-2.5">
                      <span className="font-bold text-[#0A1C2E] flex items-center gap-1.5 font-serif text-sm">
                        <Clock className="w-4 h-4 text-[#D9381E]" />
                        Revision Timetable Updated
                      </span>
                      <span className="badge-vermilion text-[10px]">Saved</span>
                    </div>

                    <div className="space-y-1.5 text-xs text-[#334E68]">
                      <div>
                        • New available budget: <strong>{m.actionRun.tool_result.available_minutes} minutes</strong>
                      </div>
                      <div>
                        • Active scheduled tasks: <strong>{m.actionRun.tool_result.tasks?.length || 0} tasks</strong> ({m.actionRun.tool_result.scheduled_minutes} min scheduled)
                      </div>
                      {m.actionRun.tool_result.deferred_tasks && m.actionRun.tool_result.deferred_tasks.length > 0 && (
                        <div className="text-[#D9381E] font-medium">
                          • Deferred to 'For later': {m.actionRun.tool_result.deferred_tasks.length} tasks
                        </div>
                      )}
                    </div>

                    {onSelectTab && (
                      <div className="mt-3 pt-2.5 border-t border-[#EDE3CE]">
                        <button
                          onClick={() => onSelectTab('plan')}
                          className="btn-vermilion text-xs py-2 px-4 flex items-center gap-1.5 font-bold shadow-2xs"
                        >
                          <span>View updated plan</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Start Practice Action Card */}
                {m.actionRun && m.actionRun.requested_action === 'start_practice' && m.actionRun.tool_result && (
                  <div className="mt-3.5 p-3.5 rounded bg-[#FAF6ED] border border-[#EDE3CE] text-xs font-sans">
                    <span className="font-bold text-[#0A1C2E] font-serif">Practice Session Ready</span>
                    <p className="text-[#334E68] mt-0.5">
                      Target micro-skill: {m.actionRun.tool_result.skill_id}
                    </p>
                    <button
                      onClick={() =>
                        onStartPractice(m.actionRun!.tool_result.skill_id, m.actionRun!.tool_result.assessment_id)
                      }
                      className="btn-vermilion text-xs py-1.5 px-3 mt-2 font-bold"
                    >
                      Open practice questions
                    </button>
                  </div>
                )}

                <div
                  className={`text-[10px] mt-2.5 font-mono ${
                    isUser ? 'text-[#9FB3C8] text-right' : 'text-[#627D98]'
                  }`}
                >
                  {m.timestamp}
                </div>
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-white border border-[#EDE3CE] flex items-center justify-center text-[#D9381E] shadow-2xs">
              <PenTool className="w-4 h-4" />
            </div>
            <div className="bg-white border border-[#EDE3CE] rounded px-4 py-3 flex items-center gap-2.5 text-xs text-[#627D98] shadow-2xs font-sans">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#D9381E]" />
              <span>Reviewing your question & consulting textbook notes...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="p-3.5 bg-white border-t border-[#EDE3CE]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="E.g., “Explain vector components” or “I only have 30 minutes today”..."
            className="flex-1 bg-[#FAF6ED] border border-[#EDE3CE] rounded px-3.5 py-2.5 text-xs sm:text-sm text-[#0A1C2E] placeholder-[#9FB3C8] focus:outline-none focus:border-[#D9381E] font-sans"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn-vermilion py-2.5 px-4 text-xs sm:text-sm font-bold shadow-2xs font-sans"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Ask mentor</span>
          </button>
        </form>
      </div>
    </div>
  );
};
