import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getModule, getLesson, completeLesson, getModuleProgress } from '../api';

function ModulePage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [module, setModule] = useState(null);
  const [activeLesson, setActiveLesson] = useState(null);
  const [lessonContent, setLessonContent] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState(null);

  // Fetch module + progress
  useEffect(() => {
    setLoading(true);
    Promise.all([getModule(slug), getModuleProgress(slug)])
      .then(([modRes, progRes]) => {
        setModule(modRes.data);
        setProgress(progRes.data);
        // Auto-select first lesson
        if (modRes.data.lessons?.length > 0) {
          loadLesson(modRes.data.lessons[0]);
        }
      })
      .catch(err => setError(err.response?.data?.detail || 'Failed to load module.'))
      .finally(() => setLoading(false));
  }, [slug]);

  const loadLesson = (lesson) => {
    setActiveLesson(lesson);
    getLesson(lesson.id)
      .then(res => setLessonContent(res.data))
      .catch(() => setLessonContent(null));
  };

  const handleComplete = async () => {
    if (!activeLesson) return;
    setCompleting(true);
    try {
      await completeLesson(activeLesson.id);
      // Refresh module and progress
      const [modRes, progRes] = await Promise.all([getModule(slug), getModuleProgress(slug)]);
      setModule(modRes.data);
      setProgress(progRes.data);
      // Update active lesson's completed status locally
      const updated = modRes.data.lessons.find(l => l.id === activeLesson.id);
      if (updated) setActiveLesson(updated);
    } catch (err) {
      // ignore
    } finally {
      setCompleting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center p-8">
        <div className="bg-red-900/30 border border-red-700 rounded-xl p-8 text-center max-w-md">
          <p className="text-red-300 text-lg">⚠️ {error}</p>
          <Link to="/learning" className="mt-4 inline-block px-6 py-2 bg-slate-700 rounded-lg text-white hover:bg-slate-600 transition-colors">← Back</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white flex flex-col lg:flex-row">
      {/* Sidebar */}
      <aside className="lg:w-80 xl:w-96 bg-slate-900/80 border-r border-slate-800 p-6 lg:min-h-screen overflow-y-auto">
        <Link to="/learning" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">← All Modules</Link>
        <h2 className="mt-4 text-xl font-bold text-white">{module?.title}</h2>
        <p className="mt-1 text-sm text-slate-400">{module?.difficulty}</p>

        {/* Progress bar */}
        {progress && (
          <div className="mt-4">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>{progress.lessons_done}/{progress.total} lessons</span>
              <span>{Math.round((progress.lessons_done / progress.total) * 100)}%</span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                style={{ width: `${(progress.lessons_done / progress.total) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Lesson list */}
        <ul className="mt-6 space-y-1">
          {module?.lessons?.map(lesson => (
            <li key={lesson.id}>
              <button
                onClick={() => loadLesson(lesson)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm flex items-center gap-2 transition-colors ${
                  activeLesson?.id === lesson.id
                    ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <span className={`w-5 h-5 shrink-0 rounded-full border-2 flex items-center justify-center text-xs ${
                  lesson.completed
                    ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400'
                    : 'border-slate-600'
                }`}>
                  {lesson.completed ? '✓' : ''}
                </span>
                <span className="truncate">{lesson.title}</span>
              </button>
            </li>
          ))}
        </ul>

        {/* Quiz button */}
        {progress?.quiz_unlocked && (
          <button
            onClick={() => navigate(`/learning/${slug}/quiz`)}
            className="mt-6 w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 font-semibold text-white transition-all shadow-lg shadow-indigo-500/20"
          >
            🎯 Take Quiz
          </button>
        )}
        {progress && !progress.quiz_unlocked && (
          <div className="mt-6 px-4 py-3 rounded-xl bg-slate-800/60 border border-slate-700 text-center text-sm text-slate-400">
            🔒 Complete all lessons to unlock the quiz
          </div>
        )}
      </aside>

      {/* Content area */}
      <main className="flex-1 p-6 lg:p-10 overflow-y-auto">
        {lessonContent ? (
          <div>
            <h1 className="text-3xl font-bold text-white mb-6">{lessonContent.title}</h1>
            <div className="prose prose-invert prose-slate max-w-none text-slate-300 leading-relaxed text-lg whitespace-pre-line">
              {lessonContent.content}
            </div>

            {/* Mark complete button */}
            <div className="mt-10 flex items-center gap-4">
              {lessonContent.completed ? (
                <span className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-900/30 border border-emerald-700 text-emerald-400 text-sm font-medium">
                  ✓ Completed
                </span>
              ) : (
                <button
                  onClick={handleComplete}
                  disabled={completing}
                  className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {completing ? 'Saving…' : '✓ Mark as Complete'}
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-64 text-slate-500">
            Select a lesson from the sidebar
          </div>
        )}
      </main>
    </div>
  );
}

export default ModulePage;
