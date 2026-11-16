import React from 'react';
import { Bookmark, RotateCcw, Clock } from 'lucide-react';
import { Profile } from '../api';

interface HeaderProps {
  profile: Profile | null;
  onUpdateMinutes: (mins: number) => void;
  onResetSession: () => void;
  activeTab: string;
  onSelectTab: (tab: string) => void;
  isLlmActive: boolean;
  agentModel?: string | null;
}

export const Header: React.FC<HeaderProps> = ({
  profile,
  onUpdateMinutes,
  onResetSession,
  activeTab,
  onSelectTab,
}) => {
  return (
    <header className="border-b border-[#EDE3CE] bg-[#FBF7EE]/95 sticky top-0 z-50 backdrop-blur-sm">
      <div className="container py-3">
        {/* Top Masthead */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-[#FAF6ED] border border-[#DFD3B9] flex items-center justify-center text-[#D9381E] shadow-xs">
              <Bookmark className="w-5 h-5 fill-[#D9381E]/15" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-[#0A1C2E] font-serif">
                  PathPilot
                </h1>
                <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-[#F5EFE0] text-[#334E68] border border-[#EDE3CE]">
                  Physics Textbook
                </span>
              </div>
              <p className="text-xs text-[#627D98] font-sans">
                A student's guide & recovery companion for JEE Physics
              </p>
            </div>
          </div>

          {/* Student Bookkeeping Controls */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Study Time Allocation */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#FFFFFF] border border-[#EDE3CE] text-xs shadow-2xs">
              <Clock className="w-3.5 h-3.5 text-[#D9381E]" />
              <span className="text-[#334E68] font-medium font-sans">Daily budget:</span>
              <select
                aria-label="Daily study time"
                className="bg-transparent text-[#0A1C2E] font-semibold focus:outline-none cursor-pointer pr-1 font-mono"
                value={profile?.daily_minutes || 45}
                onChange={(e) => onUpdateMinutes(Number(e.target.value))}
              >
                <option value={15}>15 mins</option>
                <option value={30}>30 mins</option>
                <option value={45}>45 mins</option>
                <option value={60}>60 mins</option>
                {profile && ![15, 30, 45, 60].includes(profile.daily_minutes) && (
                  <option value={profile.daily_minutes}>{profile.daily_minutes} mins</option>
                )}
              </select>
            </div>

            {/* Reset Session */}
            <button
              onClick={onResetSession}
              className="text-xs py-1.5 px-2.5 rounded bg-[#FAF6ED] hover:bg-[#F5EFE0] border border-[#EDE3CE] text-[#627D98] hover:text-[#0A1C2E] flex items-center gap-1.5 transition-colors font-sans"
              title="Start a fresh anonymous session"
              aria-label="Start a fresh anonymous session"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Start fresh</span>
            </button>
          </div>
        </div>

        {/* Chapter Bookmark Navigation */}
        <nav
          aria-label="Textbook chapters"
          className="flex items-center gap-1.5 mt-3 pt-2 border-t border-[#EDE3CE] overflow-x-auto scrollbar-none"
        >
          {[
            { id: 'diagnostic', label: '§ 1. Diagnostic' },
            { id: 'plan', label: "§ 2. Today's Plan" },
            { id: 'mentor', label: '§ 3. Margin Notes & Mentor' },
            { id: 'practice', label: '§ 4. Practice Sets' },
            { id: 'scenarios', label: 'Appendix: Reference Cutoffs' },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => onSelectTab(tab.id)}
                className={`px-3.5 py-1.5 text-xs font-semibold rounded transition-all whitespace-nowrap font-sans ${
                  isActive
                    ? 'bg-[#102A43] text-white shadow-xs'
                    : 'text-[#334E68] hover:bg-[#F5EFE0] hover:text-[#0A1C2E]'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
