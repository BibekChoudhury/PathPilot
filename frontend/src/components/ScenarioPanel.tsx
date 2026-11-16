import React, { useState } from 'react';
import { Landmark, Search, AlertCircle, ShieldAlert, CheckCircle, ExternalLink, Info, BookMarked } from 'lucide-react';
import { api, ScenarioResult } from '../api';

export const ScenarioPanel: React.FC = () => {
  const [rank, setRank] = useState<number>(1500);
  const [cohortKey, setCohortKey] = useState<string>('nitt_crl_open_os_2024');
  const [rankType, setRankType] = useState<string>('CRL');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!Number.isInteger(rank) || rank <= 0) {
      setError('Please enter a valid positive rank integer.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.compareRank(rank, cohortKey, rankType);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Scenario comparison failed');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-textbook max-w-4xl mx-auto p-5 sm:p-7 bg-white border-[#EDE3CE] shadow-textbook space-y-6 animate-fade-in font-sans">
      {/* Appendix Masthead */}
      <div className="border-b-2 border-[#102A43] pb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="badge-navy text-[10px] font-mono">
            Appendix A
          </span>
          <span className="text-xs text-[#627D98] font-mono">
            Back-of-Book Reference Tables • JoSAA 2024
          </span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold text-[#0A1C2E] font-serif flex items-center gap-2">
          <BookMarked className="w-6 h-6 text-[#D9381E]" />
          Historical College Cutoff Reference
        </h2>
        <p className="text-xs sm:text-sm text-[#627D98] mt-1 leading-relaxed">
          Compare a target JEE Main Common Rank List (CRL) rank against published JoSAA opening and closing ranks.
          This reference section evaluates historical cutoff thresholds; it does not calculate admission probabilities.
        </p>
      </div>

      {/* Cohort & Rank Query Form */}
      <form onSubmit={handleCompare} className="p-5 rounded bg-[#FAF6ED] border border-[#EDE3CE] space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          {/* Cohort Selector */}
          <div className="sm:col-span-2">
            <label htmlFor="scenario-cohort" className="block text-xs font-bold text-[#0A1C2E] mb-1 font-serif">
              Published Reference Cohort
            </label>
            <select
              id="scenario-cohort"
              value={cohortKey}
              onChange={(e) => setCohortKey(e.target.value)}
              className="w-full bg-white border border-[#EDE3CE] rounded px-3 py-2 text-xs sm:text-sm text-[#0A1C2E] focus:outline-none focus:border-[#D9381E] font-sans"
            >
              <option value="nitt_crl_open_os_2024">
                NIT Tiruchirappalli (JoSAA 2024 Round 5, OPEN, Other State)
              </option>
              <option value="invalid_cohort_synthetic">
                [Unsupported Demo Cohort — Validation Test]
              </option>
            </select>
          </div>

          {/* Rank Type */}
          <div>
            <label htmlFor="scenario-rank-type" className="block text-xs font-bold text-[#0A1C2E] mb-1 font-serif">
              Rank List
            </label>
            <select
              id="scenario-rank-type"
              value={rankType}
              onChange={(e) => setRankType(e.target.value)}
              className="w-full bg-white border border-[#EDE3CE] rounded px-3 py-2 text-xs sm:text-sm text-[#0A1C2E] focus:outline-none focus:border-[#D9381E] font-sans"
            >
              <option value="CRL">JEE Main CRL (Required)</option>
              <option value="OBC_NCL">OBC-NCL Category (Incompatible)</option>
              <option value="SC">SC Category (Incompatible)</option>
              <option value="ADVANCED_CRL">JEE Advanced CRL (Incompatible)</option>
            </select>
          </div>
        </div>

        {/* Integer Rank Input */}
        <div>
          <label htmlFor="scenario-rank" className="block text-xs font-bold text-[#0A1C2E] mb-1 font-serif">
            Target or Actual JEE Main Rank (CRL Positive Integer)
          </label>
          <div className="flex gap-2.5">
            <input
              id="scenario-rank"
              type="number"
              min={1}
              max={1500000}
              value={rank}
              onChange={(e) => setRank(Number(e.target.value))}
              className="flex-1 bg-white border border-[#EDE3CE] rounded px-4 py-2.5 text-sm text-[#0A1C2E] focus:outline-none focus:border-[#D9381E] font-mono"
              placeholder="E.g., 1500"
            />
            <button
              type="submit"
              disabled={loading}
              className="btn-vermilion text-xs sm:text-sm px-6 flex items-center gap-1.5 font-bold shadow-2xs"
            >
              <Search className="w-4 h-4" />
              <span>Lookup Cutoff</span>
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-[#627D98]">
          <Info className="w-3.5 h-3.5 text-[#D9381E] shrink-0" />
          <span>
            Example: Rank <strong>1,500</strong> is outside CSE closing cutoff (1,224) and meets ECE (3,546) and EEE (6,040) closing cutoffs.
          </span>
        </div>
      </form>

      {/* Error Notice */}
      {error && (
        <div className="p-4 bg-[#FDF2F0] border border-[#F8C8C2] rounded text-xs text-[#9C2C16] flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-[#D9381E] shrink-0 mt-0.5" />
          <div>
            <strong className="block text-[#D9381E] font-bold">Validation notice:</strong>
            {error}
          </div>
        </div>
      )}

      {/* Scannable Results Reference Table */}
      {result && (
        <div className="space-y-4 animate-fade-in font-sans">
          {/* Metadata Plate */}
          <div className="flex flex-wrap items-center justify-between text-xs text-[#334E68] bg-[#FAF6ED] p-3.5 rounded border border-[#EDE3CE]">
            <div>
              Reference: <strong className="text-[#0A1C2E] font-serif text-sm">{result.cohort_name}</strong>
            </div>
            <div>
              Quota: <span className="font-mono font-bold text-[#102A43]">{result.quota}</span> • Pool: <span className="font-mono font-bold text-[#102A43]">{result.seat_category}</span>
            </div>
            <a
              href={result.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-[#D9381E] hover:underline font-bold"
            >
              <span>JoSAA 2024 Source</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {/* Program Cutoff Entries */}
          <div className="space-y-3">
            {result.rows.map((row, idx) => {
              const isMet = row.status === 'at_or_better';
              return (
                <div
                  key={idx}
                  className={`p-4 sm:p-5 rounded border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    isMet
                      ? 'bg-[#F0F8F3] border-[#BEE3CD]'
                      : 'bg-white border-[#EDE3CE]'
                  }`}
                >
                  <div>
                    <h3 className="text-base font-bold text-[#0A1C2E] font-serif">{row.institution}</h3>
                    <p className="text-xs sm:text-sm text-[#334E68]">{row.program}</p>
                    <div className="text-xs text-[#627D98] mt-1 font-mono">
                      Opening: {row.opening_rank} • Closing cutoff: <strong className="text-[#0A1C2E]">{row.closing_rank}</strong>
                    </div>
                  </div>

                  <div className="sm:text-right shrink-0">
                    <span className={isMet ? 'badge-sage text-xs' : 'badge-vermilion text-xs'}>
                      {isMet ? 'At or Better Than Cutoff' : 'Outside Closing Rank'}
                    </span>
                    <div className="text-xs text-[#627D98] mt-1 font-mono">
                      {isMet
                        ? `Within cutoff by ${row.difference} ranks`
                        : `${row.difference} ranks outside threshold`}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Reference Disclaimer */}
          <div className="p-3.5 rounded bg-[#FAF6ED] border border-[#EDE3CE] text-[11px] text-[#627D98] flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-[#D9381E] shrink-0 mt-0.5" />
            <div>
              <strong className="text-[#334E68]">Historical reference disclaimer:</strong> {result.disclaimer}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
