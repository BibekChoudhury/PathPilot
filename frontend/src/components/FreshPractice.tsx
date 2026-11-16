import React, { useState, useEffect } from 'react';
import { Target, CheckCircle2, XCircle, ArrowRight, RefreshCw, AlertCircle, Sparkles, BookOpen } from 'lucide-react';
import { api, Assessment, QuestionPublic, AnswerResult, SkillEvidence } from '../api';

interface FreshPracticeProps {
  initialSkillId?: string;
  initialAssessmentId?: string;
  skills: SkillEvidence[];
  onCompletePractice: () => void;
  onSelectTab?: (tab: string) => void;
}

export const FreshPractice: React.FC<FreshPracticeProps> = ({
  initialSkillId = 'vector_components',
  initialAssessmentId,
  skills,
  onCompletePractice,
  onSelectTab,
}) => {
  const [selectedSkill, setSelectedSkill] = useState<string>(initialSkillId);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<AnswerResult | null>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPageTurning, setIsPageTurning] = useState<boolean>(false);

  const startPractice = async (skillId: string, assessmentId?: string) => {
    setSelectedSkill(skillId);
    setLoading(true);
    setError(null);
    setAssessment(null);
    setFeedback(null);
    setSelectedOption(null);

    try {
      const ass = assessmentId ? await api.getAssessment(assessmentId) : await api.startAssessment('practice', skillId);
      setAssessment(ass);
      setCurrentIndex(ass.answered_items);
    } catch (err: any) {
      setError(err.message || 'Failed to start practice set.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialAssessmentId) {
      void startPractice(initialSkillId, initialAssessmentId);
    }
  }, [initialAssessmentId, initialSkillId]);

  const currentItem: QuestionPublic | undefined = assessment?.items[currentIndex];

  const handleSelectOption = async (optionId: string) => {
    if (!assessment || !currentItem || feedback || submitting) return;

    setSelectedOption(optionId);
    setSubmitting(true);
    setError(null);

    try {
      const idempKey = `prac-${assessment.id}-${currentItem.id}-${optionId}`;
      const res = await api.submitAnswer(assessment.id, currentItem.id, optionId, idempKey);
      setFeedback(res);
      onCompletePractice();
    } catch (err: any) {
      setError(err.message || 'Submission error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (!assessment) return;
    setIsPageTurning(true);
    setTimeout(() => {
      setFeedback(null);
      setSelectedOption(null);
      setCurrentIndex((index) => index + 1);
      if (feedback?.is_completed) onCompletePractice();
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

  const isCompleted = assessment && currentIndex >= assessment.items.length;
  const currentSkillEvidence = skills.find((s) => s.skill_id === selectedSkill);

  return (
    <div className="card-textbook max-w-4xl mx-auto p-5 sm:p-7 bg-white border-[#EDE3CE] shadow-textbook space-y-6 animate-fade-in font-sans">
      {/* Skill Tabs */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2 border-b border-[#EDE3CE] pb-3">
          <div>
            <h2 className="text-xl font-bold text-[#0A1C2E] font-serif flex items-center gap-2">
              <Target className="w-5 h-5 text-[#D9381E]" />
              Targeted Practice Sets
            </h2>
            <p className="text-xs text-[#627D98] mt-0.5">
              3 fresh, unattempted physics problems per set to verify mastery after revision.
            </p>
          </div>
          <span className="badge-vermilion text-[10px]">
            Independent Practice Ledger
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {skills.map((s) => {
            const isSelected = selectedSkill === s.skill_id;
            return (
              <button
                disabled={loading || submitting}
                key={s.skill_id}
                onClick={() => startPractice(s.skill_id)}
                className={`p-3.5 rounded border text-left transition-all ${
                  isSelected
                    ? 'bg-[#FAF6ED] border-[#D9381E] shadow-2xs'
                    : 'bg-white border-[#EDE3CE] hover:bg-[#FAF6ED]/50 text-[#334E68]'
                }`}
              >
                <div className="text-sm font-bold font-serif text-[#0A1C2E]">{s.title}</div>
                <div className="text-[11px] text-[#627D98] mt-2 flex items-center justify-between font-mono">
                  <span>Diag: {s.diagnostic_correct}/{s.diagnostic_total}</span>
                  <span className="text-[#D9381E] font-bold">Prac: {s.practice_correct}/{s.practice_total}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {loading && (
        <div className="text-center py-8">
          <RefreshCw className="w-7 h-7 text-[#D9381E] animate-spin mx-auto mb-2" />
          <p className="text-xs text-[#627D98]">Opening practice problem set...</p>
        </div>
      )}

      {error && (
        <div className="p-3.5 bg-[#FDF2F0] border border-[#F8C8C2] rounded text-xs text-[#9C2C16] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Practice Question Card (Matching Diagnostic Pattern) */}
      {!loading && assessment && !isCompleted && currentItem && (
        <div className={`p-5 sm:p-6 rounded border border-[#EDE3CE] bg-[#FFFFFF] shadow-2xs space-y-5 transition-opacity duration-150 ${isPageTurning ? 'opacity-40 translate-y-1' : 'opacity-100 translate-y-0'}`}>
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#EDE3CE] pb-3">
            <div>
              <span className="text-xs font-mono font-bold text-[#D9381E] uppercase tracking-wider block mb-0.5">
                Practice Item {currentIndex + 1} of {assessment.total_items}
              </span>
              <h3 className="text-base font-bold text-[#0A1C2E] font-serif">
                {currentSkillEvidence?.title || selectedSkill}
              </h3>
            </div>

            {/* Sequence indicators */}
            <div className="flex items-center gap-1.5" aria-label="Practice progress">
              {Array.from({ length: assessment.total_items }).map((_, idx) => (
                <div
                  key={idx}
                  className={`w-7 h-7 rounded text-xs flex items-center justify-center font-mono font-bold ${
                    idx < currentIndex
                      ? 'bg-[#FDF2F0] text-[#D9381E] border border-[#F8C8C2]'
                      : idx === currentIndex
                      ? 'bg-[#102A43] text-white'
                      : 'bg-[#FAF6ED] text-[#9FB3C8] border border-[#EDE3CE]'
                  }`}
                >
                  {idx < currentIndex ? '✓' : idx + 1}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-lg font-serif text-[#0A1C2E] leading-relaxed">
              {currentItem.stem}
            </h4>
          </div>

          <div className="space-y-3" role="radiogroup" aria-label="Practice choices">
            {currentItem.options.map((opt) => {
              let optStyle = "bg-[#FAF6ED]/60 hover:bg-[#FAF6ED] border-[#EDE3CE] text-[#102A43]";
              if (feedback) {
                if (opt.id === feedback.correct_option) {
                  optStyle = "bg-[#F0F8F3] border-[#BEE3CD] text-[#1A5336] font-semibold";
                } else if (opt.id === selectedOption && !feedback.correctness) {
                  optStyle = "bg-[#FDF2F0] border-[#F8C8C2] text-[#9C2C16]";
                } else {
                  optStyle = "bg-[#FAF6ED]/30 border-[#EDE3CE] text-[#9FB3C8] opacity-60";
                }
              } else if (selectedOption === opt.id) {
                optStyle = "bg-[#FDF2F0] border-[#D9381E] text-[#D9381E] font-semibold";
              }

              return (
                <button
                  key={opt.id}
                  disabled={submitting || feedback !== null}
                  onClick={() => handleSelectOption(opt.id)}
                  className={`w-full text-left p-3.5 sm:p-4 rounded border transition-all flex items-start gap-3.5 min-h-[50px] ${optStyle}`}
                >
                  <span
                    className={`w-7 h-7 rounded flex items-center justify-center text-xs font-mono font-bold shrink-0 ${
                      feedback && opt.id === feedback.correct_option
                        ? 'bg-[#1A5336] text-white'
                        : feedback && opt.id === selectedOption && !feedback.correctness
                        ? 'bg-[#D9381E] text-white'
                        : selectedOption === opt.id
                        ? 'bg-[#D9381E] text-white'
                        : 'bg-[#EDE3CE] text-[#334E68]'
                    }`}
                  >
                    {opt.id}
                  </span>
                  <span className="text-sm sm:text-base pt-0.5 leading-snug flex-1 font-sans">
                    {opt.text}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Boxed Worked Solution */}
          {feedback && (
            <div
              role="alert"
              className={`worked-solution-box ${
                feedback.correctness ? 'worked-solution-correct' : 'worked-solution-incorrect'
              } page-turn`}
            >
              <div className="flex items-center gap-2 mb-1.5 font-bold font-serif text-sm">
                {feedback.correctness ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-[#1A5336]" />
                    <span className="text-[#1A5336]">Worked Solution — Correct</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 text-[#D9381E]" />
                    <span className="text-[#D9381E]">Worked Solution & Correction</span>
                    {feedback.distractor_tag && (
                      <span className="badge-vermilion text-[10px] ml-auto font-sans font-bold">
                        {feedback.distractor_tag}
                      </span>
                    )}
                  </>
                )}
              </div>
              <p className="text-xs sm:text-sm text-[#334E68] leading-relaxed pl-6 font-sans">
                {feedback.explanation}
              </p>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#EDE3CE]">
            <span className="text-[11px] text-[#627D98] font-mono">
              Keyboard: 1–4 or A–D • Enter to advance
            </span>
            {feedback && (
              <button
                onClick={handleNext}
                className="btn-vermilion text-xs py-2 px-5 flex items-center gap-2 font-bold shadow-2xs"
              >
                <span>{currentIndex + 1 < assessment.total_items ? 'Next practice question' : 'Finish practice set'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Practice Completed View (Shows Practice Score Separately) */}
      {isCompleted && (
        <div className="text-center py-8 bg-[#F0F8F3] rounded border border-[#BEE3CD] p-6 animate-fade-in">
          <CheckCircle2 className="w-10 h-10 text-[#1A5336] mx-auto mb-2" />
          <h3 className="text-xl font-bold text-[#1A5336] font-serif mb-1">
            Practice Problem Set Completed!
          </h3>
          <p className="text-xs sm:text-sm text-[#1A5336] max-w-md mx-auto mb-5 leading-relaxed font-sans">
            Your results have been recorded in the mastery ledger. Your practice score is preserved separately from your initial diagnostic baseline.
          </p>

          <div className="flex flex-wrap justify-center gap-3">
            {onSelectTab && (
              <button
                onClick={() => onSelectTab('plan')}
                className="btn-navy text-xs py-2 px-5 font-bold font-sans shadow-xs"
              >
                Return to Revision Plan
              </button>
            )}
            <button
              onClick={() => startPractice(selectedSkill)}
              className="btn-ivory text-xs py-2 px-5 font-semibold font-sans"
            >
              Retry This Problem Set
            </button>
          </div>
        </div>
      )}

      {!assessment && !loading && (
        <div className="text-center py-8 bg-[#FAF6ED] rounded border border-[#EDE3CE] p-6">
          <p className="text-xs text-[#627D98] mb-3 font-sans">
            Select a physics syllabus topic above to begin 3 targeted practice questions.
          </p>
          <button
            onClick={() => startPractice(selectedSkill)}
            className="btn-vermilion text-xs py-2.5 px-6 font-bold font-sans shadow-xs"
          >
            Start Practice on {currentSkillEvidence?.title || selectedSkill}
          </button>
        </div>
      )}
    </div>
  );
};
