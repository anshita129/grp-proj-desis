function BadgeUnlockModal({ badges, onClose }) {
  if (!badges || badges.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-indigo-500/40 rounded-2xl p-8 max-w-sm w-full mx-4 text-center shadow-2xl shadow-indigo-500/20 animate-scale-in">
        <div className="text-5xl mb-4">🏆</div>
        <h2 className="text-2xl font-bold bg-gradient-to-r from-amber-400 to-yellow-300 bg-clip-text text-transparent">
          Badge{badges.length > 1 ? 's' : ''} Unlocked!
        </h2>

        <div className="mt-6 space-y-4">
          {badges.map(badge => (
            <div key={badge.id} className="bg-slate-800/60 border border-amber-500/30 rounded-xl p-4 flex items-center gap-4">
              <span className="text-3xl">
                {badge.icon_name === 'star' ? '⭐' : badge.icon_name === 'trophy' ? '🏆' : badge.icon_name === 'crown' ? '👑' : '🎖️'}
              </span>
              <div className="text-left">
                <p className="font-semibold text-white">{badge.name}</p>
                <p className="text-sm text-slate-400">{badge.description}</p>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={onClose}
          className="mt-6 px-8 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 font-semibold text-slate-900 transition-all"
        >
          Awesome!
        </button>
      </div>

      <style>{`
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        @keyframes scale-in { from { opacity: 0; transform: scale(0.85); } to { opacity: 1; transform: scale(1); } }
        .animate-fade-in { animation: fade-in 0.3s ease-out; }
        .animate-scale-in { animation: scale-in 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
      `}</style>
    </div>
  );
}

export default BadgeUnlockModal;
