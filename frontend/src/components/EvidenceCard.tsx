import React from 'react';
import { Target, BookOpen, ArrowUpRight } from 'lucide-react';
import { SkillEvidence } from '../api';

interface EvidenceCardProps {
  skills: SkillEvidence[];
  onStartPractice: (skillId: string) => void;
  onAskExplain: (skillId: string) => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ skills, onStartPractice, onAskExplain }) => {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#EDE3CE] pb-3">
        <div>
          <h3 className="text-base font-bold text-[#0A1C2E] font-serif flex items-center gap-2">
            <Target className="w-4 h-4 text-[#D9381E]" />
            Micro-Skill Diagnostic Evidence & Mastery Ledger
          </h3>
          <p className="text-xs text-[#627D98] mt-0.5 font-sans">
            Evaluated across 3 foundational JEE Physics syllabus topics. Diagnostic baseline and subsequent practice are recorded separately.
          </p>
        </div>
        <span className="badge-vermilion text-[10px]">
          Sample Caveat: 3 Items per Topic
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {skills.map((skill) => {
          const isProficient = skill.status === 'proficient';
          const isUnassessed = skill.status === 'not_assessed';

          return (
            <div
              key={skill.skill_id}
              className={`card-textbook flex flex-col justify-between p-5 border transition-all ${
                isProficient
                  ? 'border-[#BEE3CD] bg-[#FFFFFF]'
                  : isUnassessed
                  ? 'border-[#EDE3CE] bg-[#FAF6ED]'
                  : 'border-[#F8C8C2] bg-[#FFFFFF]'
              }`}
            >
              <div>
                {/* Header Status & Score */}
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={
                      isProficient
                        ? 'badge-sage'
                        : isUnassessed
                        ? 'badge-navy'
                        : 'badge-vermilion'
                    }
                  >
                    {isProficient ? 'Proficient' : isUnassessed ? 'Not Assessed' : 'Needs Revision'}
                  </span>
                  <span className="text-xs text-[#627D98] font-mono">
                    Score: {skill.diagnostic_correct}/{skill.diagnostic_total}
                  </span>
                </div>

                {/* Skill Title */}
                <h4 className="font-bold text-[#0A1C2E] text-base mb-1 font-serif leading-snug">
                  {skill.title}
                </h4>

                {/* Diagnostic Score Progress Bar */}
                <div className="w-full bg-[#F5EFE0] rounded-full h-1.5 my-3 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      isProficient ? 'bg-[#1A5336]' : 'bg-[#D9381E]'
                    }`}
                    style={{
                      width: `${(skill.diagnostic_correct / (skill.diagnostic_total || 1)) * 100}%`,
                    }}
                  />
                </div>

                {/* Attempted & Practice Ledger */}
                <div className="text-xs text-[#334E68] space-y-1.5 mb-3 font-sans">
                  <div className="flex justify-between py-1 border-b border-[#FAF6ED]">
                    <span className="text-[#627D98]">Diagnostic:</span>
                    <span className="font-semibold text-[#0A1C2E]">
                      {skill.diagnostic_attempted} of {skill.diagnostic_total} attempted
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#FAF6ED]">
                    <span className="text-[#627D98]">Subsequent practice:</span>
                    <span className="font-semibold text-[#D9381E]">
                      {skill.practice_attempted > 0
                        ? `${skill.practice_correct} of ${skill.practice_attempted} correct`
                        : 'None yet'}
                    </span>
                  </div>
                </div>

                {/* Identified Misconceptions */}
                {skill.misconceptions && skill.misconceptions.length > 0 && (
                  <div className="mb-3">
                    <span className="text-[11px] font-bold text-[#D9381E] block mb-1 font-sans">
                      Identified Misconceptions:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {skill.misconceptions.map((tag, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded bg-[#FDF2F0] border border-[#F8C8C2] text-[11px] text-[#9C2C16] font-mono"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Honest Limitation Caveat */}
                <p className="text-[11px] text-[#627D98] italic bg-[#FAF6ED] p-2.5 rounded border border-[#EDE3CE] mb-4 font-sans leading-relaxed">
                  {skill.evidence_caveat}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-3 border-t border-[#EDE3CE]">
                <button
                  onClick={() => onAskExplain(skill.skill_id)}
                  className="btn-ivory text-xs py-1.5 px-3 flex-1 flex items-center justify-center gap-1.5 font-sans"
                >
                  <BookOpen className="w-3.5 h-3.5 text-[#334E68]" />
                  <span>Notes</span>
                </button>
                <button
                  onClick={() => onStartPractice(skill.skill_id)}
                  className="btn-vermilion text-xs py-1.5 px-3 flex-1 flex items-center justify-center gap-1.5 font-sans"
                >
                  <ArrowUpRight className="w-3.5 h-3.5" />
                  <span>Practice</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
