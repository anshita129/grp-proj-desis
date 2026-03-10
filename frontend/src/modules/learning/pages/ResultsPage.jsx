import { useState, useEffect } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import { getAttempt } from '../api';
import BadgeUnlockModal from '../components/BadgeUnlockModal';

function ResultsPage() {
  const { attemptId } = useParams();
  const location = useLocation();
  const passedState = location.state; // may have score, passed, newly_awarded_badges, slug

  const [attempt, setAttempt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showBadgeModal, setShowBadgeModal] = useState(false);
  const [newBadges, setNewBadges] = useState([]);

  useEffect(() => {
    // Check for badge modal from navigation state
    if (passedState?.newly_awarded_badges?.length > 0) {
      setNewBadges(passedState.newly_awarded_badges);
      setShowBadgeModal(true);
    }
    // Fetch full attempt details
    getAttempt(attemptId)
      .then(res => setAttempt(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [attemptId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const passed = attempt?.passed;
  const score = attempt?.score;
  const total = attempt?.total_questions;
  const pct = total > 0 ? Math.round((score / total) * 100) : 0;
  const slug = attempt?.module_slug || passedState?.slug;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
      {/* Badge unlock modal */}
      {showBadgeModal && (
        <BadgeUnlockModal badges={newBadges} onClose={() => setShowBadgeModal(false)} />
      )}

      <div className="max-w-3xl mx-auto px-6 py-10">
        {/* Score Card */}
        <div className={`rounded-2xl p-8 text-center border ${
          passed
            ? 'bg-emerald-900/20 border-emerald-700/50'
            : 'bg-red-900/20 border-red-700/50'
        }`}>
          <div className="text-6xl font-bold">
            {passed ? '🎉' : '😔'}
          </div>
          <h1 className={`mt-4 text-3xl font-bold ${passed ? 'text-emerald-400' : 'text-red-400'}`}>
            {passed ? 'Quiz Passed!' : 'Quiz Failed'}
          </h1>
          <p className="mt-2 text-5xl font-extrabold text-white">
            {score}<span className="text-2xl text-slate-400">/{total}</span>
          </p>
          <p className="mt-1 text-lg text-slate-400">{pct}% correct</p>

          {!passed && (
            <p className="mt-4 text-sm text-red-300">
              You need at least 7/{total} to pass. Keep studying and try again!
            </p>
          )}
          {passed && (
            <p className="mt-4 text-sm text-emerald-300">
              ✅ Module Complete — great work!
            </p>
          )}

          {/* Action buttons */}
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            {!passed && slug && (
              <Link
                to={`/learning/${slug}/quiz`}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 font-semibold text-white transition-all"
              >
                🔄 Retake Quiz
              </Link>
            )}
            {passed && (
              <Link
                to="/learning"
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 font-semibold text-white transition-all"
              >
                → Next Module
              </Link>
            )}
            <Link
              to="/learning"
              className="px-6 py-3 rounded-xl bg-slate-800 border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-white transition-all"
            >
              ← All Modules
            </Link>
          </div>
        </div>

        {/* Answer Breakdown */}
        {attempt?.answers && (
          <div className="mt-10">
            <h2 className="text-xl font-bold text-white mb-4">Answer Breakdown</h2>
            <div className="space-y-4">
              {attempt.answers.map((a, idx) => (
                <div
                  key={idx}
                  className={`rounded-xl p-5 border ${
                    a.is_correct
                      ? 'bg-emerald-900/10 border-emerald-800/40'
                      : 'bg-red-900/10 border-red-800/40'
                  }`}
                >
                  <p className="text-sm font-medium text-white">
                    <span className={`mr-2 ${a.is_correct ? 'text-emerald-400' : 'text-red-400'}`}>
                      {a.is_correct ? '✓' : '✗'}
                    </span>
                    Q{idx + 1}. {a.question_text}
                  </p>
                  <p className="mt-2 text-sm text-slate-400">
                    Your answer: <span className={a.is_correct ? 'text-emerald-300' : 'text-red-300'}>{a.selected_text}</span>
                  </p>
                  {!a.is_correct && (
                    <p className="mt-1 text-sm text-emerald-400">
                      Correct answer: {a.correct_choice}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ResultsPage;
