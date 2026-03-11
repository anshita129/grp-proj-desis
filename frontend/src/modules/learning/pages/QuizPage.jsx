import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuiz, submitAttempt } from '../api';

function QuizPage() {
  const { slug } = useParams();
  const navigate = useNavigate();

  const [status, setStatus] = useState('loading'); // loading | ready | answering | submitting | error
  const [quiz, setQuiz] = useState(null);
  const [selections, setSelections] = useState({});
  const [error, setError] = useState('');

  useEffect(() => {
    getQuiz(slug)
      .then(res => {
        setQuiz(res.data);
        setStatus('ready');
      })
      .catch(err => {
        setError(err.response?.data?.detail || 'Failed to load quiz.');
        setStatus('error');
      });
  }, [slug]);

  const handleSelect = (questionId, choiceId) => {
    if (status === 'submitting') return;
    const next = { ...selections, [questionId]: choiceId };
    setSelections(next);
    if (status === 'ready') setStatus('answering');
  };

  const allAnswered = quiz && Object.keys(selections).length === quiz.questions.length;

  const handleSubmit = async () => {
    if (!allAnswered || !quiz) return;
    setStatus('submitting');
    try {
      const answers = Object.entries(selections).map(([qid, cid]) => ({
        question_id: parseInt(qid),
        choice_id: parseInt(cid),
      }));
      const res = await submitAttempt(quiz.id, { answers });
      navigate(`/learning/results/${res.data.attempt_id}`, {
        state: {
          score: res.data.score,
          total: res.data.total,
          passed: res.data.passed,
          pass_mark: res.data.pass_mark,
          newly_awarded_badges: res.data.newly_awarded_badges,
          slug,
        },
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed.');
      setStatus('error');
    }
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center p-8">
        <div className="bg-red-900/30 border border-red-700 rounded-xl p-8 text-center max-w-md">
          <p className="text-red-300 text-lg">⚠️ {error}</p>
          <button
            onClick={() => { setStatus('loading'); setError(''); window.location.reload(); }}
            className="mt-4 px-6 py-2 bg-red-700 hover:bg-red-600 rounded-lg text-white transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
      <div className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          {quiz.title}
        </h1>
        <p className="mt-2 text-slate-400">Answer all {quiz.questions.length} questions. You need {quiz.pass_mark}/{quiz.questions.length} to pass.</p>

        {/* Questions */}
        <div className="mt-8 space-y-8">
          {quiz.questions.map((q, idx) => (
            <div key={q.id} className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
              <p className="text-base font-medium text-white">
                <span className="text-indigo-400 mr-2">Q{idx + 1}.</span>
                {q.text}
              </p>
              <div className="mt-4 space-y-2">
                {q.choices.map(c => {
                  const selected = selections[q.id] === c.id;
                  return (
                    <label
                      key={c.id}
                      className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all border ${
                        selected
                          ? 'bg-indigo-600/20 border-indigo-500 text-white'
                          : 'bg-slate-900/40 border-slate-700/40 text-slate-300 hover:border-slate-600 hover:bg-slate-800/60'
                      } ${status === 'submitting' ? 'pointer-events-none opacity-60' : ''}`}
                    >
                      <input
                        type="radio"
                        name={`q-${q.id}`}
                        value={c.id}
                        checked={selected}
                        onChange={() => handleSelect(q.id, c.id)}
                        disabled={status === 'submitting'}
                        className="accent-indigo-500"
                      />
                      <span className="text-sm">{c.text}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Submit */}
        <div className="mt-10 flex justify-center">
          <button
            onClick={handleSubmit}
            disabled={!allAnswered || status === 'submitting'}
            className="px-10 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 font-semibold text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/20"
          >
            {status === 'submitting' ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Submitting…
              </span>
            ) : (
              `Submit Answers (${Object.keys(selections).length}/${quiz.questions.length})`
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuizPage;
