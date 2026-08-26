import { useState, useMemo } from 'react';
import rawData from '../public/data/latest.json';

// ── Types ────────────────────────────────────────────────────────────────────
type Stock = {
  Symbol: string;
  Company: string;
  Score?: string | null;
  'Weighted Score'?: number | null;
  Action?: string | null;
  Industry: string;
  'Current Price'?: number | null;
  ATH?: number | null;
  '52W Return'?: number | null;
  'Beats Nifty500'?: boolean | null;
  'Beats Sector'?: boolean | null;
  'Record PAT?'?: boolean | null;
  'Price Quality Score'?: number | null;
  'Fundamental Score'?: number | null;
  'RS Composite Score'?: number | null;
  'Risk Flags'?: string | null;
  'Pass Risk Filter'?: boolean | null;
  Beta?: number | null;
  'Alpha (Annual)'?: number | null;
  'RS Line Trend'?: string | null;
  'PAT CAGR'?: number | null;
  'Data Status'?: string | null;
  _sheet: string;
};

type ScreenerData = {
  generated_at: string;
  universe_size: number;
  counts: Record<string, number>;
  stocks: Stock[];
};

// ── Safe data loader ───────────────────────────────────────────────────────
const typedData: ScreenerData = {
  generated_at: (rawData as any).generated_at ?? 'Unknown',
  universe_size: (rawData as any).universe_size ?? 0,
  counts: (rawData as any).counts ?? {},
  stocks: Array.isArray((rawData as any).stocks) ? (rawData as any).stocks : [],
};

// ── Formatters ───────────────────────────────────────────────────────────────
const isValidNum = (n: unknown): n is number =>
  typeof n === 'number' && !Number.isNaN(n);

const fmtPct = (n: number | null | undefined) =>
  isValidNum(n) ? `${(n * 100).toFixed(2)}%` : '—';

const fmtPrice = (n: number | null | undefined) =>
  isValidNum(n) ? `₹${n.toFixed(2)}` : '—';

const fmtNum = (n: number | null | undefined, digits = 2) =>
  isValidNum(n) ? n.toFixed(digits) : '—';

const timeAgo = (dateStr: string) => {
  if (!dateStr || dateStr === 'Unknown' || dateStr === 'Not yet run') return 'Unknown';
  try {
    const then = new Date(dateStr);
    const now = new Date();
    const mins = Math.floor((now.getTime() - then.getTime()) / 60000);
    if (mins < 2) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  } catch {
    return dateStr;
  }
};

type TabKey = 'CONVICTION' | '3/3' | '2/3' | 'ALL' | 'RISK_REJECT' | 'EXIT';

// ── Component ──────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [tab, setTab] = useState<TabKey>('CONVICTION');
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    let rows = typedData.stocks;
    if (tab === 'CONVICTION') rows = rows.filter((r) => r.Action === 'CONVICTION BUY');
    if (tab === '3/3') rows = rows.filter((r) => r.Score === '3/3');
    if (tab === '2/3') rows = rows.filter((r) => r.Score === '2/3');
    if (tab === 'RISK_REJECT') rows = rows.filter((r) => r.Action === 'RISK REJECT');
    if (tab === 'EXIT') rows = rows.filter((r) => ['0/3', '1/3'].includes(r.Score ?? ''));
    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter(
        (r) =>
          (r.Symbol ?? '').toLowerCase().includes(q) ||
          (r.Company ?? '').toLowerCase().includes(q) ||
          (r.Industry ?? '').toLowerCase().includes(q)
      );
    }
    return rows;
  }, [tab, search]);

  const counts = typedData.counts;
  const freshness = timeAgo(typedData.generated_at);
  const isStale = freshness.includes('h') || freshness.includes('d') || freshness === 'Unknown';

  const actionBadge = (action?: string | null, score?: string | null) => {
    if (action === 'CONVICTION BUY') return 'bg-purple-600 text-white';
    if (score === '3/3') return 'bg-emerald-500 text-white';
    if (score === '2/3') return 'bg-amber-500 text-white';
    if (action === 'RISK REJECT') return 'bg-slate-500 text-white';
    return 'bg-red-400 text-white';
  };

  const scoreBadge = (score?: string | null) => {
    if (score === '3/3') return 'bg-emerald-100 text-emerald-700 border border-emerald-200';
    if (score === '2/3') return 'bg-amber-100 text-amber-700 border border-amber-200';
    if (score === '1/3') return 'bg-orange-100 text-orange-700 border border-orange-200';
    return 'bg-red-100 text-red-700 border border-red-200';
  };

  const actionLabel = (action?: string | null) => {
    if (!action) return '—';
    if (action === 'CONVICTION BUY') return 'CONVICTION';
    return action.split(' - ')[0] ?? '—';
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Mehta 3/3 Advanced Screener</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm text-slate-500">
                Last updated: {typedData.generated_at || 'Unknown'}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                isStale ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
              }`}>
                {freshness}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Auto-refreshes at 4 PM IST on weekdays. Universe: {typedData.universe_size || typedData.stocks.length} stocks.
            </p>
          </div>
          <a
            href="https://github.com/thejaduijin/growth_scanner/actions"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition"
          >
            ▶️ Run Screener Now
          </a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          {[
            { label: 'Conviction', value: counts.CONVICTION ?? 0, color: 'bg-purple-600' },
            { label: '3/3 Super', value: counts['3/3'] ?? 0, color: 'bg-emerald-500' },
            { label: '2/3 Hold', value: counts['2/3'] ?? 0, color: 'bg-amber-500' },
            { label: '1/3 Weak', value: counts['1/3'] ?? 0, color: 'bg-orange-400' },
            { label: '0/3 Exit', value: counts['0/3'] ?? 0, color: 'bg-red-400' },
            { label: 'Risk Reject', value: counts.RISK_REJECT ?? 0, color: 'bg-slate-500' },
          ].map((s) => (
            <div key={s.label} className={`${s.color} rounded-xl p-4 text-white shadow-sm`}>
              <div className="text-white/80 text-xs font-medium">{s.label}</div>
              <div className="text-2xl font-bold mt-1">{s.value}</div>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4 flex flex-col lg:flex-row gap-3 items-center justify-between">
          <div className="flex flex-wrap gap-2">
            {([
              { key: 'CONVICTION' as TabKey, label: '🎯 Conviction' },
              { key: '3/3' as TabKey, label: '⭐ 3/3 Super' },
              { key: '2/3' as TabKey, label: '🔶 2/3 Hold' },
              { key: 'ALL' as TabKey, label: '📋 All' },
              { key: 'RISK_REJECT' as TabKey, label: '⚠️ Risk' },
              { key: 'EXIT' as TabKey, label: '❌ Exit' },
            ]).map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-3 py-2 rounded-lg text-xs sm:text-sm font-semibold transition ${
                  tab === t.key
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <input
            type="text"
            placeholder="Search symbol, company, industry..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full lg:w-64 px-4 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-xs sm:text-sm">
              <thead className="bg-slate-100 text-slate-600 uppercase text-[10px] sm:text-xs font-semibold">
                <tr>
                  <th className="px-3 py-3 text-left">Symbol</th>
                  <th className="px-3 py-3 text-left">Company</th>
                  <th className="px-3 py-3 text-center">Action</th>
                  <th className="px-3 py-3 text-center">Score</th>
                  <th className="px-3 py-3 text-left">Industry</th>
                  <th className="px-3 py-3 text-right">Price</th>
                  <th className="px-3 py-3 text-right">ATH</th>
                  <th className="px-3 py-3 text-right">52W</th>
                  <th className="px-3 py-3 text-center">Price Q</th>
                  <th className="px-3 py-3 text-center">Fund Q</th>
                  <th className="px-3 py-3 text-center">RS</th>
                  <th className="px-3 py-3 text-center">Wtd</th>
                  <th className="px-3 py-3 text-center">Nifty</th>
                  <th className="px-3 py-3 text-center">Sector</th>
                  <th className="px-3 py-3 text-center">PAT</th>
                  <th className="px-3 py-3 text-center">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={16} className="px-4 py-8 text-center text-slate-400">
                      No stocks match your filters.
                    </td>
                  </tr>
                )}
                {filtered.map((row, i) => {
                  const isConviction = row.Action === 'CONVICTION BUY';
                  return (
                    <tr key={i} className={`hover:bg-slate-50 transition ${isConviction ? 'bg-purple-50/50' : ''}`}>
                      <td className="px-3 py-3 font-bold text-slate-900 whitespace-nowrap">{row.Symbol ?? '—'}</td>
                      <td className="px-3 py-3 text-slate-700 whitespace-nowrap">{row.Company ?? '—'}</td>
                      <td className="px-3 py-3 text-center">
                        <span className={`inline-block px-2 py-1 rounded-full text-[10px] font-bold ${actionBadge(row.Action, row.Score)}`}>
                          {actionLabel(row.Action)}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-center">
                        <span className={`inline-block px-2 py-1 rounded text-[10px] font-bold ${scoreBadge(row.Score)}`}>
                          {row.Score ?? '—'}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-slate-600 whitespace-nowrap">{row.Industry ?? '—'}</td>
                      <td className="px-3 py-3 text-right font-mono text-slate-700">{fmtPrice(row['Current Price'])}</td>
                      <td className="px-3 py-3 text-right font-mono text-slate-500">{fmtPrice(row.ATH)}</td>
                      <td className="px-3 py-3 text-right font-mono text-slate-700">{fmtPct(row['52W Return'])}</td>
                      <td className="px-3 py-3 text-center">
                        <ScoreDot score={row['Price Quality Score']} />
                      </td>
                      <td className="px-3 py-3 text-center">
                        <ScoreDot score={row['Fundamental Score']} />
                      </td>
                      <td className="px-3 py-3 text-center">
                        <ScoreDot score={row['RS Composite Score']} />
                      </td>
                      <td className="px-3 py-3 text-center font-mono font-bold text-slate-700">
                        {fmtNum(row['Weighted Score'])}
                      </td>
                      <td className="px-3 py-3 text-center">{row['Beats Nifty500'] ? '✅' : '❌'}</td>
                      <td className="px-3 py-3 text-center">{row['Beats Sector'] ? '✅' : '❌'}</td>
                      <td className="px-3 py-3 text-center">{row['Record PAT?'] ? '✅' : '❌'}</td>
                      <td className="px-3 py-3 text-center">
                        {row['Pass Risk Filter'] === false ? (
                          <span className="text-red-500 font-bold text-[10px]" title={row['Risk Flags'] ?? ''}>
                            FAIL
                          </span>
                        ) : (
                          <span className="text-emerald-500 text-[10px]">PASS</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-500 flex justify-between">
            <span>Showing {filtered.length} of {typedData.stocks.length} stocks</span>
            <span>Universe: {typedData.universe_size || typedData.stocks.length}</span>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs text-slate-500">
          <div className="bg-white rounded-lg border border-slate-200 p-3">
            <div className="font-semibold text-slate-700 mb-1">Score Dots</div>
            <div className="flex gap-3">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> ≥70 Pass</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400" /> 50-69</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400" /> &lt;50</span>
            </div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-3">
            <div className="font-semibold text-slate-700 mb-1">Pillars</div>
            <div>Price Q = Breakout quality. Fund Q = PAT + OCF. RS = Relative Strength vs Nifty + Sector.</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-3">
            <div className="font-semibold text-slate-700 mb-1">Conviction Buy</div>
            <div>3/3 score + Weighted Score ≥ 2.4 + passes all risk gates.</div>
          </div>
        </div>
      </main>
    </div>
  );
}

function ScoreDot({ score }: { score?: number | null }) {
  if (!isValidNum(score)) {
    return <span className="inline-block w-2 h-2 rounded-full bg-slate-300" title="N/A" />;
  }
  const color = score >= 70 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-400' : 'bg-red-400';
  return (
    <span className="inline-flex items-center gap-1">
      <span className={`w-2 h-2 rounded-full ${color}`} />
      <span className="font-mono text-[10px]">{score.toFixed(0)}</span>
    </span>
  );
}