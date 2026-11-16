import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, ArrowRight, RefreshCw, AlertCircle, BookOpen, PenTool, Check, Lightbulb } from 'lucide-react';
import { api, Assessment, QuestionPublic, AnswerResult, SkillEvidence } from '../api';

interface DiagnosticProps {
  onComplete: () => void;
  onRefreshEvidence: () => void;
  skills?: SkillEvidence[];
}

export const Diagnostic: React.FC<DiagnosticProps> = ({ onComplete, onRefreshEvidence, skills = [] }) => {
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<AnswerResult | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPageTurning, setIsPageTurning] = useState<boolean>(false);

  useEffect(() => {
    loadOrStartDiagnostic();
  }, []);

  const loadOrStartDiagnostic = async () => {
    try {
      setLoading(true);
      setError(null);
      const ass = await api.startAssessment('diagnostic');
      setAssessment(ass);
      setCurrentIndex(ass.answered_items);
      setFeedback(null);
      setSelectedOption(null);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize diagnostic quiz.');
    } finally {
      setLoading(false);
    }
  };

  const currentItem: QuestionPublic | undefined = assessment?.items[currentIndex];

  const handleSelectOption = async (optionId: string) => {
    if (!assessment || !currentItem || feedback || submitting) return;

    setSelectedOption(optionId);
    setSubmitting(true);
    setError(null);

    try {
      const idempKey = `diag-${assessment.id}-${currentItem.id}-${optionId}`;
      const res = await api.submitAnswer(assessment.id, currentItem.id, optionId, idempKey);
      setFeedback(res);
      onRefreshEvidence();
    } catch (err: any) {
      setError(err.message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (!assessment) return;

    // Short page turn transition
    setIsPageTurning(true);
    setTimeout(() => {
      setFeedback(null);
      setSelectedOption(null);
      if (currentIndex + 1 < assessment.items.length) {
        setCurrentIndex(currentIndex + 1);
      } else {
        setCurrentIndex(assessment.items.length);
        setAssessment({ ...assessment, status: 'completed', answered_items: assessment.total_items });
        onComplete();
      }
      setIsPageTurning(false);
    }, 160);
  };

  // Keyboard shortcut listener (1-4, A-D, Enter)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.repeat || e.altKey || e.ctrlKey || e.metaKey || e.isComposing) return;
      if (e.target instanceof HTMLElement && e.target.closest('input, select, textarea, button, a, [contenteditable]')) return;

      if (feedback && e.key === 'Enter') {
        e.preventDefault();
        handleNext();
        return;
      }

      if (!feedback && !submitting && currentItem) {
        const key = e.key.toUpperCase();
        if (['A', 'B', 'C', 'D'].includes(key)) {
          handleSelectOption(key);
        } else if (['1', '2', '3', '4'].includes(e.key)) {
          const mapped = ['A', 'B', 'C', 'D'][parseInt(e.key, 10) - 1];
          handleSelectOption(mapped);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [feedback, submitting, currentItem, currentIndex]);

  const skillNameMap: Record<string, string> = {
    vector_components: '§ 1.1 Vector Components & Decomposition',
    vector_addition: '§ 1.2 Vector Addition & Resultants',
    constant_accel_1d: '§ 2.1 1D Motion with Constant Acceleration',
  };

  const skillTeacherNotes: Record<string, string> = {
    vector_components: "Margin note: Remember Fx = |F|·cos(θ) only when θ is measured from the positive x-axis. Watch quadrant signs carefully!",
    vector_addition: "Margin note: Never add magnitudes directly unless vectors are strictly parallel. Break into components first.",
    constant_accel_1d: "Margin note: Verify that acceleration is constant before applying kinematic equations: v = u + at, s = ut + ½at².",
  };

  if (loading) {
    return (
      <div className="card-textbook text-center py-12 p-6 border-[#EDE3CE] bg-white">
        <RefreshCw className="w-8 h-8 text-[#D9381E] animate-spin mx-auto mb-3" />
        <h3 className="text-lg font-bold text-[#0A1C2E] font-serif">Opening Physics Textbook...</h3>
        <p className="text-xs text-[#627D98] mt-1 font-sans">Turning to Chapter 1: Diagnostic Assessment</p>
      </div>
    );
  }

  if (error && !assessment) {
    return (
      <div className="card-textbook text-center py-8 p-6 border-[#F8C8C2] bg-[#FDF2F0]">
        <AlertCircle className="w-10 h-10 text-[#D9381E] mx-auto mb-2" />
        <p className="text-[#9C2C16] text-sm mb-4 font-sans">{error}</p>
        <button onClick={loadOrStartDiagnostic} className="btn-vermilion text-xs">
          Retry Loading Chapter
        </button>
      </div>
    );
  }

  const isQuizComplete = assessment && assessment.status === 'completed' && !feedback && currentIndex >= assessment.items.length;
  const weakestSkill = skills.find((s) => s.status === 'needs_practice') || skills[0];

  // =================== SKILL RESULTS ("WHAT TO REVISE") ===================
  if (isQuizComplete) {
    return (
      <div className="card-textbook max-w-3xl mx-auto p-6 sm:p-8 bg-white border-[#EDE3CE] shadow-textbook animate-fade-in">
        {/* Textbook Chapter Header */}
        <div className="border-b-2 border-[#102A43] pb-4 mb-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="badge-vermilion text-[10px]">
              Diagnostic Complete
            </span>
            <span className="text-xs text-[#627D98] font-mono">
              9 of 9 Questions Answered
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-[#0A1C2E] font-serif">
            What to Revise
          </h2>
          <p className="text-xs text-[#627D98] mt-1 font-sans">
            Diagnostic summary & priority syllabus recommendations based on your verified performance.
          </p>
        </div>

        {/* Priority Topic to Work on First */}
        {weakestSkill && (
          <div className="p-5 rounded bg-[#FAF6ED] border-l-4 border-[#D9381E] border-t border-r border-b border-[#EDE3CE] mb-6">
            <div className="flex items-center gap-2 mb-1.5">
              <PenTool className="w-4 h-4 text-[#D9381E]" />
              <span className="text-xs font-bold text-[#D9381E] uppercase tracking-wider font-sans">
                Topic to revise first
              </span>
            </div>
            <h3 className="text-lg font-bold text-[#0A1C2E] font-serif">
              {weakestSkill.title}
            </h3>
            <p className="text-xs sm:text-sm text-[#334E68] mt-1 leading-relaxed font-sans">
              Diagnostic score: <strong>{weakestSkill.diagnostic_correct} of {weakestSkill.diagnostic_total} correct</strong>.
              Your personalized revision timetable places this foundation topic first so you master prerequisites before composite problems.
            </p>
          </div>
        )}

        {/* Attempted Summary Table */}
        <div className="border border-[#EDE3CE] rounded overflow-hidden mb-6 text-xs font-sans">
          <div className="p-3 bg-[#F5EFE0] flex justify-between font-bold text-[#0A1C2E] border-b border-[#EDE3CE]">
            <span>Micro-Skill Revision Targets</span>
            <span>Attempted / Score</span>
          </div>
          <div className="divide-y divide-[#EDE3CE]">
            {skills.map((s) => (
              <div key={s.skill_id} className="p-3.5 flex items-center justify-between bg-white hover:bg-[#FAF6ED]/50 transition-colors">
                <div>
                  <div className="font-semibold text-[#0A1C2E] text-sm font-serif">{s.title}</div>
                  <div className="text-[#627D98] text-[11px] mt-0.5">
                    {s.diagnostic_attempted} of {s.diagnostic_total} questions attempted
                    {s.misconceptions && s.misconceptions.length > 0 && (
                      <span className="ml-2 text-[#D9381E] font-mono">
                        (Misconception: {s.misconceptions.join(', ')})
                      </span>
                    )}
                  </div>
                </div>
                <span className={s.status === 'proficient' ? 'badge-sage' : 'badge-vermilion'}>
                  {s.diagnostic_correct} / {s.diagnostic_total} correct
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Visible Small-Sample Caveat Note */}
        <div className="p-3.5 rounded bg-[#FAF6ED] border border-[#EDE3CE] text-xs text-[#627D98] leading-relaxed mb-6 font-sans">
          <strong className="text-[#334E68]">Note on sample size:</strong> This preliminary evaluation uses 9 targeted diagnostic items (3 questions per micro-skill). It identifies immediate conceptual misunderstandings to seed today's study plan; durable mastery is confirmed through fresh practice sets.
        </div>

        {/* Primary Student Action */}
        <div className="pt-2">
          <button
            onClick={onComplete}
            className="btn-vermilion w-full py-3.5 text-sm font-bold flex items-center justify-center gap-2 shadow-sm font-sans"
          >
            <span>Open today’s revision plan</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  if (!currentItem) {
    return (
      <div className="card-textbook text-center py-8 p-6">
        <p className="text-[#334E68] font-sans">Diagnostic chapter ready.</p>
        <button onClick={onComplete} className="btn-vermilion mt-4 text-xs font-sans">
          Open today’s revision plan
        </button>
      </div>
    );
  }

  const totalItems = assessment?.total_items || 9;

  return (
    <div className={`card-textbook max-w-4xl mx-auto p-5 sm:p-7 bg-white border-[#EDE3CE] shadow-textbook transition-opacity duration-150 ${isPageTurning ? 'opacity-40 translate-y-1' : 'opacity-100 translate-y-0'}`}>
      {/* Mobile Top Chapter Header & Compact Progress Strip */}
      <div className="lg:hidden mb-5 pb-3 border-b border-[#EDE3CE]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono font-bold text-[#D9381E] uppercase tracking-wider">
            Question {currentIndex + 1} of {totalItems}
          </span>
          <span className="text-[11px] text-[#627D98] font-sans">Sequential Chapter</span>
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {Array.from({ length: totalItems }).map((_, idx) => (
            <div
              key={idx}
              className={`w-7 h-7 rounded text-xs flex items-center justify-center font-mono font-bold shrink-0 ${
                idx < currentIndex
                  ? 'bg-[#FDF2F0] text-[#D9381E] border border-[#F8C8C2]'
                  : idx === currentIndex
                  ? 'bg-[#102A43] text-white shadow-xs'
                  : 'bg-[#FAF6ED] text-[#9FB3C8] border border-[#EDE3CE]'
              }`}
            >
              {idx < currentIndex ? '✓' : idx + 1}
            </div>
          ))}
        </div>
      </div>

      {/* Main Textbook Layout: 2 Columns on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Question & Worked Solution (lg:col-span-8) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Chapter Section Title */}
          <div>
            <div className="flex items-center gap-2 text-xs font-mono uppercase text-[#D9381E] font-bold tracking-wider mb-1">
              <span>Diagnostic</span>
              <span>•</span>
              <span>Question {currentIndex + 1} of {totalItems}</span>
            </div>
            <h3 className="text-base font-serif font-bold text-[#0A1C2E]">
              {skillNameMap[currentItem.skill_id] || currentItem.skill_id}
            </h3>
          </div>

          {/* Question Stem (Generous Space & STIX Serif) */}
          <div className="py-1">
            <h2 className="text-lg sm:text-xl font-serif text-[#0A1C2E] leading-relaxed">
              {currentItem.stem}
            </h2>
          </div>

          {/* Answer Option Buttons */}
          <div className="space-y-3" role="radiogroup" aria-label="Answer choices">
            {currentItem.options.map((option) => {
              let btnStyle = "bg-[#FAF6ED]/60 hover:bg-[#FAF6ED] border-[#EDE3CE] text-[#102A43]";

              if (feedback) {
                if (option.id === feedback.correct_option) {
                  btnStyle = "bg-[#F0F8F3] border-[#BEE3CD] text-[#1A5336] font-semibold";
                } else if (option.id === selectedOption && !feedback.correctness) {
                  btnStyle = "bg-[#FDF2F0] border-[#F8C8C2] text-[#9C2C16]";
                } else {
                  btnStyle = "bg-[#FAF6ED]/30 border-[#EDE3CE] text-[#9FB3C8] opacity-60";
                }
              } else if (selectedOption === option.id) {
                btnStyle = "bg-[#FDF2F0] border-[#D9381E] text-[#D9381E] font-semibold";
              }

              return (
                <button
                  key={option.id}
                  role="radio"
                  aria-checked={selectedOption === option.id}
                  disabled={submitting || feedback !== null}
                  onClick={() => handleSelectOption(option.id)}
                  className={`w-full text-left p-3.5 sm:p-4 rounded border transition-all flex items-start gap-3.5 min-h-[52px] ${btnStyle}`}
                >
                  <span
                    className={`w-7 h-7 rounded flex items-center justify-center text-xs font-mono font-bold shrink-0 ${
                      feedback && option.id === feedback.correct_option
                        ? 'bg-[#1A5336] text-white'
                        : feedback && option.id === selectedOption && !feedback.correctness
                        ? 'bg-[#D9381E] text-white'
                        : selectedOption === option.id
                        ? 'bg-[#D9381E] text-white'
                        : 'bg-[#EDE3CE] text-[#334E68]'
                    }`}
                  >
                    {option.id}
                  </span>
                  <span className="text-sm sm:text-base pt-0.5 leading-snug flex-1 font-sans">
                    {option.text}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Boxed Worked Solution Callout (Revealed Immediately on Answer) */}
          {feedback && (
            <div
              role="alert"
              className={`worked-solution-box ${
                feedback.correctness ? 'worked-solution-correct' : 'worked-solution-incorrect'
              } page-turn`}
            >
              <div className="flex items-center gap-2 mb-2 font-bold text-sm font-serif">
                {feedback.correctness ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-[#1A5336]" />
                    <span className="text-[#1A5336]">Worked Solution — Correct!</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 text-[#D9381E]" />
                    <span className="text-[#D9381E]">Worked Solution & Correction</span>
                    {feedback.distractor_tag && (
                      <span className="badge-vermilion text-[10px] ml-auto font-sans font-bold">
                        Misconception: {feedback.distractor_tag}
                      </span>
                    )}
                  </>
                )}
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-[#334E68] font-sans pl-6">
                {feedback.explanation}
              </p>
            </div>
          )}

          {/* Mobile Continue Action */}
          <div className="lg:hidden pt-2">
            {feedback ? (
              <button
                onClick={handleNext}
                className="btn-vermilion w-full py-3 text-xs font-bold flex items-center justify-center gap-2 shadow-sm font-sans"
              >
                <span>{currentIndex + 1 < totalItems ? 'Continue to next question' : 'Finish & view revision plan'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <div className="text-xs text-[#627D98] flex items-center gap-2 font-sans">
                <span>Keyboard:</span>
                <kbd className="px-1.5 py-0.5 rounded bg-[#FAF6ED] border border-[#EDE3CE] text-[#334E68] font-mono text-[11px]">1–4</kbd>
                <span>or</span>
                <kbd className="px-1.5 py-0.5 rounded bg-[#FAF6ED] border border-[#EDE3CE] text-[#334E68] font-mono text-[11px]">A–D</kbd>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Signature Chapter Margin (lg:col-span-4) */}
        <aside className="hidden lg:block lg:col-span-4 border-l-2 border-[#D9381E]/30 pl-6 space-y-6">
          <div>
            <span className="text-[11px] font-mono uppercase text-[#D9381E] font-bold tracking-wider block mb-1">
              Chapter Margin
            </span>
            <h4 className="text-sm font-bold text-[#0A1C2E] font-serif">
              Progress & Study Notes
            </h4>
          </div>

          {/* Sequential Chapter Progress Strip */}
          <div className="space-y-1.5">
            {Array.from({ length: totalItems }).map((_, idx) => {
              const isDone = idx < currentIndex;
              const isCurrent = idx === currentIndex;

              return (
                <div
                  key={idx}
                  className={`flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors font-sans ${
                    isCurrent
                      ? 'bg-[#102A43] text-white font-semibold'
                      : isDone
                      ? 'bg-[#FAF6ED] text-[#334E68]'
                      : 'text-[#9FB3C8]'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <span className="font-mono text-[11px] w-4">
                      {isDone ? '✓' : idx + 1}
                    </span>
                    <span>Question {idx + 1}</span>
                  </span>
                  <span className="text-[10px] uppercase font-mono">
                    {isDone ? 'Completed' : isCurrent ? 'Active' : 'Sequential'}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Dynamic Margin Annotation Note */}
          <div className="p-3.5 rounded bg-[#FAF6ED] border border-[#EDE3CE]">
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#D9381E] mb-1 font-sans">
              <Lightbulb className="w-3.5 h-3.5" />
              <span>Margin Note:</span>
            </div>
            <p className="margin-note">
              {feedback?.distractor_tag
                ? `Attention: Identified ${feedback.distractor_tag}. Always confirm your trigonometric projection triangle!`
                : skillTeacherNotes[currentItem.skill_id] || "Work through each step systematically on scratch paper before selecting your option."}
            </p>
          </div>

          {/* Next Action in Chapter Margin */}
          {feedback && (
            <div className="pt-2 page-turn">
              <button
                onClick={handleNext}
                className="btn-vermilion w-full py-3 text-xs font-bold flex items-center justify-center gap-2 shadow-sm font-sans"
              >
                <span>{currentIndex + 1 < totalItems ? 'Continue to next question' : 'Finish & view plan'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <div className="text-[11px] text-[#627D98] text-center mt-2 font-sans">
                Press <kbd className="px-1 py-0.5 rounded bg-[#FAF6ED] border border-[#EDE3CE] font-mono text-[#334E68]">Enter ↵</kbd> to continue
              </div>
            </div>
          )}

          {!feedback && (
            <div className="text-[11px] text-[#627D98] leading-relaxed font-sans">
              Select an answer to reveal the boxed worked solution and chapter explanation.
            </div>
          )}
        </aside>
      </div>
    </div>
  );
};
