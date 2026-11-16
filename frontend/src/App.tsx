import React, { useState, useEffect } from 'react';
import { api, Profile, ProgressData } from './api';
import { Header } from './components/Header';
import { Diagnostic } from './components/Diagnostic';
import { EvidenceCard } from './components/EvidenceCard';
import { DailyPlan } from './components/DailyPlan';
import { MentorChat } from './components/MentorChat';
import { FreshPractice } from './components/FreshPractice';
import { ScenarioPanel } from './components/ScenarioPanel';
import { RefreshCw, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [activeTab, setActiveTab] = useState<string>('diagnostic');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isLlmActive, setIsLlmActive] = useState<boolean>(false);
  const [agentModel, setAgentModel] = useState<string | null>(null);
  const [practiceSkillId, setPracticeSkillId] = useState<string>('vector_components');

  const [practiceAssessmentId, setPracticeAssessmentId] = useState<string>();
  const [mentorSkillId, setMentorSkillId] = useState<string>();

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      setLoading(true);
      setError(null);

      const [prog, health] = await Promise.all([api.initSession(), api.getHealth().catch(() => null)]);
      setIsLlmActive(Boolean(health?.llm_provider_configured));
      setAgentModel(health?.agent_router_model || null);
      setProfile(prog.profile);
      setProgress(prog);

      // If returning student has already completed diagnostic and has a plan, resume at plan
      if (prog.diagnostic_completed && prog.current_plan) {
        setActiveTab('plan');
      }
    } catch (err: any) {
      console.error('App init error:', err);
      setError(err.message || 'Failed to initialize session. Make sure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshProgress = async () => {
    try {
      const prog = await api.getProgress();
      setProgress(prog);
      if (prog.profile) setProfile(prog.profile);
      return prog;
    } catch (err) {
      console.error('Failed to refresh progress:', err);
    }
  };

  const handleUpdateMinutes = async (mins: number) => {
    try {
      if (progress?.current_plan) {
        await api.replan(mins, progress.current_plan.version, 'Updated study budget');
      } else {
        setProfile(await api.updateProfile(mins));
      }
      await handleRefreshProgress();
    } catch (err: any) {
      alert(err.message || 'Failed to update time budget');
    }
  };

  const handleResetSession = async () => {
    if (!confirm('Start a fresh study session? This resets progress in this browser.')) {
      return;
    }
    try {
      setLoading(true);
      await api.resetSession();
      await initializeApp();
      setActiveTab('diagnostic');
    } catch (err: any) {
      alert(err.message || 'Failed to reset session');
      setLoading(false);
    }
  };

  const handleStartPractice = (skillId: string, assessmentId?: string) => {
    setPracticeSkillId(skillId);
    setPracticeAssessmentId(assessmentId);
    setActiveTab('practice');
  };

  const handleAskExplain = (skillId: string) => {
    setMentorSkillId(skillId);
    setActiveTab('mentor');
  };

  const handleCompleteDiagnostic = async () => {
    try {
      const fresh = await api.getProgress();
      if (!fresh.current_plan) {
        await api.createPlan(fresh.profile.daily_minutes);
      }
      await handleRefreshProgress();
      setActiveTab('plan');
    } catch (err) {
      console.error('Diagnostic completion error:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FBF7EE] flex flex-col items-center justify-center p-4">
        <RefreshCw className="w-8 h-8 text-[#D9381E] animate-spin mb-3" />
        <h2 className="text-lg font-bold text-[#0A1C2E] font-serif mb-1">
          Opening Your Physics Companion...
        </h2>
        <p className="text-xs text-[#627D98] font-sans">Loading your study workspace</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#FBF7EE] flex flex-col items-center justify-center p-4">
        <div className="card-textbook max-w-md text-center p-6 border-[#F8C8C2] bg-white shadow-textbook">
          <AlertCircle className="w-10 h-10 text-[#D9381E] mx-auto mb-3" />
          <h2 className="text-lg font-bold text-[#0A1C2E] font-serif mb-1">
            Connection Notice
          </h2>
          <p className="text-xs text-[#334E68] mb-5 leading-relaxed font-sans">{error}</p>
          <button onClick={initializeApp} className="btn-vermilion w-full text-xs font-bold font-sans">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FBF7EE] flex flex-col text-[#102A43] font-sans selection:bg-[#F8C8C2] selection:text-[#B82C15]">
      {/* Top Textbook Header */}
      <Header
        profile={profile}
        onUpdateMinutes={handleUpdateMinutes}
        onResetSession={handleResetSession}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isLlmActive={isLlmActive}
        agentModel={agentModel}
      />

      {/* Main Study Content */}
      <main className="container flex-1 py-6 sm:py-8 space-y-6">
        {/* Tab 1: Diagnostic & Skill Evidence */}
        {activeTab === 'diagnostic' && (
          <div className="space-y-8 animate-fade-in">
            <Diagnostic
              onComplete={handleCompleteDiagnostic}
              onRefreshEvidence={handleRefreshProgress}
              skills={progress?.skills || []}
            />

            {progress && (
              <EvidenceCard
                skills={progress.skills}
                onStartPractice={handleStartPractice}
                onAskExplain={handleAskExplain}
              />
            )}
          </div>
        )}

        {/* Tab 2: Revision Timetable */}
        {activeTab === 'plan' && (
          <div className="animate-fade-in">
            <DailyPlan
              plan={progress?.current_plan || null}
              onRefreshPlan={handleRefreshProgress}
              onSelectTab={setActiveTab}
              onStartPractice={handleStartPractice}
              onAskExplain={handleAskExplain}
            />
          </div>
        )}

        {/* Tab 3: Margin Notes & Mentor */}
        {activeTab === 'mentor' && (
          <div className="animate-fade-in">
            <MentorChat
              currentPlan={progress?.current_plan || null}
              initialSkillId={mentorSkillId}
              onPlanUpdated={handleRefreshProgress}
              onStartPractice={handleStartPractice}
              onSelectTab={setActiveTab}
            />
          </div>
        )}

        {/* Tab 4: Practice Sets */}
        {activeTab === 'practice' && (
          <div className="animate-fade-in">
            <FreshPractice
              initialSkillId={practiceSkillId}
              initialAssessmentId={practiceAssessmentId}
              skills={progress?.skills || []}
              onCompletePractice={handleRefreshProgress}
              onSelectTab={setActiveTab}
            />
          </div>
        )}

        {/* Tab 5: Reference Cutoffs (Appendix) */}
        {activeTab === 'scenarios' && (
          <div className="animate-fade-in">
            <ScenarioPanel />
          </div>
        )}
      </main>

      {/* Textbook Colophon Footer */}
      <footer className="border-t border-[#EDE3CE] bg-[#FAF6ED]/80 py-4 text-xs text-[#627D98] mt-10">
        <div className="container flex flex-wrap items-center justify-between gap-3 font-sans">
          <span>PathPilot — A Student's Companion for JEE Physics</span>
          <span>JoSAA 2024 Reference Cutoffs • 3 Evaluated Physics Micro-Skills</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
