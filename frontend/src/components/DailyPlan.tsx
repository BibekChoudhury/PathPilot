import React, { useState } from 'react';
import { CheckSquare, Square, Clock, ArrowRight, BookOpen, ArrowUpRight, Sparkles, CheckCircle2, AlertCircle, Calendar } from 'lucide-react';
import { api, Plan, Task, ReplanResult } from '../api';

interface DailyPlanProps {
  plan: Plan | null;
  onRefreshPlan: () => void;
  onSelectTab: (tab: string) => void;
  onStartPractice: (skillId: string) => void;
  onAskExplain: (skillId: string) => void;
}

export const DailyPlan: React.FC<DailyPlanProps> = ({
  plan,
  onRefreshPlan,
  onSelectTab,
  onStartPractice,
  onAskExplain,
}) => {
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);
  const [replanning, setReplanning] = useState<boolean>(false);
  const [replanNotice, setReplanNotice] = useState<{
    prevMinutes: number;
    newMinutes: number;
    deferredCount: number;
    message: string;
  } | null>(null);

  const handleToggleTask = async (task: Task) => {
    try {
      setUpdatingTaskId(task.id);
      const nextStatus = task.status === 'completed' ? 'pending' : 'completed';
      await api.updateTaskStatus(task.id, nextStatus);
      onRefreshPlan();
    } catch (err: any) {
      alert(err.message || 'Failed to update task status');
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleQuickReplan = async (minutes: number) => {
    if (!plan) return;
    const prevMins = plan.available_minutes;
    try {
      setReplanning(true);
      const res = await api.replan(
        minutes,
        plan.version,
        `Student requested timetable adjustment to ${minutes} minutes`
      );
      setReplanNotice({
        prevMinutes: prevMins,
        newMinutes: res.available_minutes,
        deferredCount: res.deferred_tasks.length,
        message: `Timetable adjusted from ${prevMins}m to ${res.available_minutes}m. ${res.deferred_tasks.length} tasks scheduled for later to prevent overload.`,
      });
      onRefreshPlan();
    } catch (err: any) {
      alert(err.message || 'Replanning failed');
    } finally {
      setReplanning(false);
    }
  };

  if (!plan) {
    return (
      <div className="card-textbook text-center py-12 max-w-xl mx-auto p-6 bg-white border-[#EDE3CE] shadow-textbook animate-fade-in">
        <div className="w-12 h-12 rounded bg-[#FAF6ED] border border-[#DFD3B9] text-[#D9381E] flex items-center justify-center mx-auto mb-3">
          <Calendar className="w-6 h-6" />
        </div>
        <h3 className="text-xl font-bold text-[#0A1C2E] font-serif mb-1">
          No Active Revision Timetable
        </h3>
        <p className="text-xs text-[#627D98] max-w-sm mx-auto mb-6 leading-relaxed font-sans">
          Complete the 9-question physics diagnostic first. PathPilot will analyze your micro-skill gaps and build your structured revision timetable for today.
        </p>
        <button
          onClick={() => onSelectTab('diagnostic')}
          className="btn-vermilion text-xs py-2.5 px-6 font-bold font-sans"
        >
          <span>Start Diagnostic Chapter</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  const completedCount = plan.tasks.filter((t) => t.status === 'completed').length;
  const nextTask = plan.tasks.find((t) => t.status === 'pending');
  const allTasksCompleted = plan.tasks.length > 0 && completedCount === plan.tasks.length;

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-fade-in font-sans">
      {/* Timetable Header Card */}
      <div className="card-textbook border-[#EDE3CE] bg-white p-5 sm:p-7 shadow-textbook">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#EDE3CE] pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="badge-vermilion text-[10px]">
                Revision Timetable
              </span>
              <span className="text-xs text-[#627D98] font-mono">
                {plan.reason}
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-[#0A1C2E] font-serif">
              Today’s Revision Plan
            </h2>
            <p className="text-xs text-[#627D98] mt-1 font-sans">
              Strict time budgeting: tasks are ordered by syllabus prerequisite and fitted to your allocated time.
            </p>
          </div>

          {/* Time & Completion Ledger */}
          <div className="flex items-center gap-4 bg-[#FAF6ED] border border-[#EDE3CE] px-4 py-3 rounded text-xs">
            <div>
              <span className="text-[#627D98] block text-[11px]">Time Scheduled</span>
              <span className="font-bold text-[#102A43] font-mono text-base">
                {plan.scheduled_minutes} / {plan.available_minutes} min
              </span>
            </div>
            <div className="w-px h-8 bg-[#EDE3CE]" />
            <div>
              <span className="text-[#627D98] block text-[11px]">Completed</span>
              <span className="font-bold text-[#1A5336] font-mono text-base">
                {completedCount} / {plan.tasks.length} tasks
              </span>
            </div>
          </div>
        </div>

        {/* Quick Timetable Presets */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[#627D98] font-medium">Adjust available time:</span>
            {[15, 30, 45, 60].map((mins) => (
              <button
                key={mins}
                disabled={replanning || plan.available_minutes === mins}
                onClick={() => handleQuickReplan(mins)}
                className={`px-3 py-1 rounded text-xs font-mono font-bold transition-all ${
                  plan.available_minutes === mins
                    ? 'bg-[#102A43] text-white shadow-xs'
                    : 'bg-[#FAF6ED] text-[#334E68] hover:bg-[#F5EFE0] border border-[#EDE3CE]'
                }`}
              >
                {mins}m
              </button>
            ))}
          </div>

          <span className="text-[11px] text-[#9FB3C8] font-mono">
            Deterministic allocation • Overflows preserved
          </span>
        </div>

        {/* Live Replan Highlight Notice (Shows actual before & after data) */}
        {replanNotice && (
          <div className="mt-4 p-3.5 rounded bg-[#FDF2F0] border-l-4 border-[#D9381E] border-t border-r border-b border-[#F8C8C2] text-xs text-[#0A1C2E] replan-highlight">
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-[#D9381E] flex items-center gap-1.5 font-sans">
                <Sparkles className="w-3.5 h-3.5" />
                Timetable Re-budgeted
              </span>
              <span className="font-mono text-[11px] text-[#627D98]">
                {replanNotice.prevMinutes}m → {replanNotice.newMinutes}m
              </span>
            </div>
            <p className="leading-relaxed text-[#334E68]">
              {replanNotice.message}
            </p>
          </div>
        )}
      </div>

      {/* Hero Next Task (Most Space & Attention) */}
      {nextTask && (
        <div className="card-textbook border-2 border-[#D9381E] bg-[#FFFFFF] p-6 sm:p-7 shadow-textbook relative overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded bg-[#D9381E] text-white text-[11px] font-mono font-bold uppercase tracking-wider">
                Next Task
              </span>
              <span className="px-2.5 py-0.5 rounded bg-[#FAF6ED] border border-[#EDE3CE] text-xs font-mono font-bold text-[#102A43] flex items-center gap-1">
                <Clock className="w-3 h-3 text-[#D9381E]" />
                {nextTask.minutes} mins
              </span>
              <span className="text-xs text-[#627D98] font-mono uppercase tracking-wider">
                {nextTask.kind}
              </span>
            </div>
          </div>

          <div className="my-2">
            <h3 className="text-xl sm:text-2xl font-bold text-[#0A1C2E] font-serif">
              {nextTask.title}
            </h3>
            <p className="text-sm sm:text-base text-[#334E68] mt-1.5 leading-relaxed font-sans">
              {nextTask.description}
            </p>
          </div>

          <div className="pt-4 flex flex-wrap items-center gap-3">
            <button
              onClick={() =>
                nextTask.kind === 'practice'
                  ? onStartPractice(nextTask.skill_id)
                  : onAskExplain(nextTask.skill_id)
              }
              className="btn-vermilion text-xs sm:text-sm py-2.5 px-5 font-bold shadow-xs flex items-center gap-2"
            >
              {nextTask.kind === 'practice' ? (
                <>
                  <ArrowUpRight className="w-4 h-4" />
                  <span>Start Practice Session ({nextTask.minutes}m)</span>
                </>
              ) : (
                <>
                  <BookOpen className="w-4 h-4" />
                  <span>Open Revision Notes ({nextTask.minutes}m)</span>
                </>
              )}
            </button>

            <button
              disabled={updatingTaskId === nextTask.id}
              onClick={() => handleToggleTask(nextTask)}
              className="btn-ivory text-xs sm:text-sm py-2.5 px-4 font-semibold text-[#334E68] hover:text-[#0A1C2E] flex items-center gap-1.5"
            >
              <CheckSquare className="w-4 h-4 text-[#1A5336]" />
              <span>Mark as completed</span>
            </button>
          </div>
        </div>
      )}

      {/* All Tasks Completed Celebration */}
      {allTasksCompleted && (
        <div className="card-textbook text-center py-7 border-[#BEE3CD] bg-[#F0F8F3] p-6">
          <CheckCircle2 className="w-9 h-9 text-[#1A5336] mx-auto mb-2" />
          <h3 className="text-lg font-bold text-[#1A5336] font-serif">
            All revision tasks completed for today!
          </h3>
          <p className="text-xs sm:text-sm text-[#1A5336] mt-1 max-w-md mx-auto">
            Excellent progress! You have completed all scheduled tasks. You can test your mastery with fresh practice sets or ask the mentor for deep concept reviews.
          </p>
        </div>
      )}

      {/* Timetable Task Ledger */}
      <div className="card-textbook border-[#EDE3CE] bg-white p-5 sm:p-6 shadow-textbook">
        <div className="flex items-center justify-between border-b border-[#EDE3CE] pb-3 mb-3">
          <h3 className="font-bold text-[#0A1C2E] text-base font-serif">
            Full Revision Timetable ({plan.tasks.length} tasks)
          </h3>
          <span className="text-xs text-[#627D98] font-mono">
            {plan.scheduled_minutes} minutes allocated
          </span>
        </div>

        <div className="space-y-2.5">
          {plan.tasks.map((task) => {
            const isCompleted = task.status === 'completed';
            const isCurrentNext = nextTask?.id === task.id;

            return (
              <div
                key={task.id}
                className={`p-4 rounded border transition-all flex items-start gap-3.5 ${
                  isCompleted
                    ? 'bg-[#FAF6ED]/50 border-[#EDE3CE] opacity-75'
                    : isCurrentNext
                    ? 'bg-[#FDF2F0]/40 border-[#F8C8C2]'
                    : 'bg-white border-[#EDE3CE] hover:border-[#DFD3B9]'
                }`}
              >
                <button
                  aria-label={isCompleted ? `Mark ${task.title} as incomplete` : `Mark ${task.title} as complete`}
                  disabled={updatingTaskId === task.id}
                  onClick={() => handleToggleTask(task)}
                  className="mt-0.5 text-[#9FB3C8] hover:text-[#D9381E] transition-colors focus:outline-none"
                >
                  {isCompleted ? (
                    <CheckSquare className="w-5 h-5 text-[#1A5336]" />
                  ) : (
                    <Square className="w-5 h-5 text-[#9FB3C8]" />
                  )}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded bg-[#FAF6ED] border border-[#EDE3CE] font-mono text-[11px] font-bold text-[#334E68]">
                      {task.minutes}m
                    </span>
                    <span className="text-[11px] font-mono uppercase text-[#627D98] font-bold">
                      {task.kind}
                    </span>
                    {isCurrentNext && (
                      <span className="badge-vermilion text-[10px]">
                        Up next
                      </span>
                    )}
                  </div>

                  <h4 className={`text-base font-medium font-serif ${isCompleted ? 'line-through text-[#627D98]' : 'text-[#0A1C2E]'}`}>
                    {task.title}
                  </h4>
                  <p className="text-xs text-[#627D98] mt-0.5 leading-relaxed font-sans">
                    {task.description}
                  </p>

                  {!isCompleted && (
                    <div className="mt-3 flex items-center gap-2">
                      <button
                        onClick={() =>
                          task.kind === 'practice' ? onStartPractice(task.skill_id) : onAskExplain(task.skill_id)
                        }
                        className="text-xs font-bold text-[#D9381E] hover:underline flex items-center gap-1 font-sans"
                      >
                        {task.kind === 'practice' ? (
                          <>
                            <span>Open practice questions</span>
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </>
                        ) : (
                          <>
                            <span>Open revision notes</span>
                            <BookOpen className="w-3.5 h-3.5" />
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* For Later (Deferred Tasks Drawer) */}
      {plan.deferred_tasks && plan.deferred_tasks.length > 0 && (
        <div className="card-textbook border-[#EDE3CE] bg-[#FAF6ED] p-5 sm:p-6 shadow-textbook">
          <div className="border-b border-[#EDE3CE] pb-3 mb-3">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-[#0A1C2E] text-base font-serif">
                For Later
              </h3>
              <span className="px-2 py-0.5 rounded bg-[#EDE3CE] text-[#334E68] text-xs font-mono font-bold">
                {plan.deferred_tasks.length} tasks deferred
              </span>
            </div>
            <p className="text-xs text-[#627D98] mt-1 font-sans">
              Deferred to upcoming revision sessions to preserve your daily budget of {plan.available_minutes} minutes without dropping syllabus coverage.
            </p>
          </div>

          <div className="space-y-2 font-sans">
            {plan.deferred_tasks.map((dt, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded bg-white border border-[#EDE3CE] text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-2xs"
              >
                <div>
                  <span className="font-semibold text-[#0A1C2E] font-serif text-sm">{dt.title}</span>
                  <span className="text-[#627D98] ml-2 font-mono">({dt.minutes} mins · {dt.kind})</span>
                </div>
                <span className="text-[11px] text-[#D9381E] bg-[#FDF2F0] px-2.5 py-0.5 rounded border border-[#F8C8C2] font-mono font-semibold shrink-0">
                  {dt.reason}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
