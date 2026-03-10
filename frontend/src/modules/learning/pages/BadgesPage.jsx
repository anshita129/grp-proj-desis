import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getBadges } from '../api';

function BadgesPage() {
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getBadges()
      .then(res => setBadges(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const ICON_MAP = { star: '⭐', trophy: '🏆', crown: '👑' };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
      <div className="max-w-3xl mx-auto px-6 py-10">
        <Link to="/learning" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">← Back to Modules</Link>
        <h1 className="mt-4 text-3xl font-bold bg-gradient-to-r from-amber-400 to-yellow-300 bg-clip-text text-transparent">
          🏆 Badges
        </h1>
        <p className="mt-2 text-slate-400">Earn badges by completing quizzes and achieving milestones.</p>

        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {badges.map(badge => (
            <div
              key={badge.id}
              className={`rounded-2xl p-6 text-center border transition-all ${
                badge.awarded
                  ? 'bg-slate-800/50 border-amber-500/40 shadow-lg shadow-amber-500/10'
                  : 'bg-slate-800/20 border-slate-700/30 opacity-50 grayscale'
              }`}
            >
              <div className="text-5xl mb-3">
                {ICON_MAP[badge.icon_name] || '🎖️'}
              </div>
              <h3 className="text-lg font-bold text-white">{badge.name}</h3>
              <p className="mt-1 text-sm text-slate-400">{badge.description}</p>
              {badge.awarded ? (
                <p className="mt-3 text-xs text-amber-400 font-medium">
                  ✓ Earned {new Date(badge.awarded_at).toLocaleDateString()}
                </p>
              ) : (
                <p className="mt-3 text-xs text-slate-500">🔒 Locked</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default BadgesPage;
