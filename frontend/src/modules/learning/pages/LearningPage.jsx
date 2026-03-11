import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getModules } from '../api';

function LearningPage() {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getModules()
      .then(res => setModules(res.data))
      .catch(err => setError(err.response?.data?.detail || 'Failed to load modules.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorBanner message={error} />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
      {/* Header */}
      <header className="px-6 py-8 md:px-12 lg:px-20">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          Learning Modules
        </h1>
        <p className="mt-2 text-slate-400 text-lg">Master the stock market — one module at a time</p>
        <div className="mt-4">
          <Link to="/learning/badges" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800/60 border border-slate-700 hover:border-indigo-500 transition-colors text-sm text-slate-300 hover:text-white">
            🏆 My Badges
          </Link>
        </div>
      </header>

      {/* Module Grid */}
      <main className="px-6 pb-16 md:px-12 lg:px-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {modules.map(mod => (
            <ModuleCard key={mod.id} module={mod} />
          ))}
        </div>
      </main>
    </div>
  );
}

const DIFFICULTY_COLORS = {
  Beginner: 'from-emerald-500 to-teal-600',
  Intermediate: 'from-amber-500 to-orange-600',
  Advanced: 'from-rose-500 to-red-600',
};

function ModuleCard({ module }) {
  const { title, slug, description, difficulty, total_lessons, lessons_done } = module;
  const pct = total_lessons > 0 ? Math.round((lessons_done / total_lessons) * 100) : 0;
  const radius = 28;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (pct / 100) * circ;

  return (
    <Link
      to={`/learning/${slug}`}
      className="group relative flex flex-col rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6 backdrop-blur-sm hover:border-indigo-500/60 hover:shadow-lg hover:shadow-indigo-500/10 transition-all duration-300 hover:-translate-y-1"
    >
      {/* Difficulty badge */}
      <span className={`self-start mb-3 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r ${DIFFICULTY_COLORS[difficulty] || 'from-gray-500 to-gray-600'} text-white`}>
        {difficulty}
      </span>

      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold text-white group-hover:text-indigo-300 transition-colors leading-tight">
            {title}
          </h2>
          <p className="mt-2 text-sm text-slate-400 line-clamp-2">{description}</p>
        </div>

        {/* Progress ring */}
        <svg width="68" height="68" className="shrink-0 -mt-1">
          <circle cx="34" cy="34" r={radius} fill="none" stroke="rgb(51 65 85)" strokeWidth="5" />
          <circle
            cx="34" cy="34" r={radius}
            fill="none"
            stroke="url(#grad)"
            strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            transform="rotate(-90 34 34)"
            className="transition-all duration-700"
          />
          <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="100%" stopColor="#c084fc" />
            </linearGradient>
          </defs>
          <text x="34" y="38" textAnchor="middle" className="fill-white text-sm font-bold">{pct}%</text>
        </svg>
      </div>

      <div className="mt-4 text-xs text-slate-500">
        {lessons_done}/{total_lessons} lessons complete
      </div>
    </Link>
  );
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-6 md:p-12 lg:p-20">
      <div className="h-10 w-64 bg-slate-800 rounded-lg animate-pulse mb-4" />
      <div className="h-5 w-96 bg-slate-800/60 rounded animate-pulse mb-8" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-48 bg-slate-800/50 rounded-2xl animate-pulse" />
        ))}
      </div>
    </div>
  );
}

function ErrorBanner({ message }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center p-8">
      <div className="bg-red-900/30 border border-red-700 rounded-xl p-8 text-center max-w-md">
        <p className="text-red-300 text-lg font-medium">⚠️ {message}</p>
        <button onClick={() => window.location.reload()} className="mt-4 px-6 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-white transition-colors">
          Retry
        </button>
      </div>
    </div>
  );
}

export default LearningPage;