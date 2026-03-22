import { Link } from "react-router-dom";

export default function HomePage() {
    const modules = [
        {
            title: "Learning",
            description: "Learn about algorithmic trading and financial markets through our interactive courses.",
            path: "/learning",
            color: "from-blue-500 to-cyan-400",
            icon: "📚"
        },
        {
            title: "Trading",
            description: "Execute trades and manage your positions in real-time across various markets.",
            path: "/trading",
            color: "from-emerald-500 to-teal-400",
            icon: "📈"
        },
        {
            title: "Portfolio",
            description: "View your assets, track performance history, and analyze your current holdings.",
            path: "/portfolio",
            color: "from-purple-500 to-violet-400",
            icon: "💼"
        },
        {
            title: "AI Agent",
            description: "Consult with our AI assistant for deep market insights and trading strategies.",
            path: "/ai",
            color: "from-amber-500 to-orange-400",
            icon: "🤖"
        },
        {
            title: "Simulation",
            description: "Test your trading strategies in a gamified, risk-free market simulation environment.",
            path: "/simulation",
            color: "from-rose-500 to-pink-400",
            icon: "🎮"
        }
    ];

    return (
        <div className="p-8 max-w-7xl mx-auto">
            <div className="mb-10">
                <h1 className="text-4xl font-bold text-white mb-2">Welcome to GRP DESIS</h1>
                <p className="text-lg text-slate-400">Your complete platform for learning and practicing algorithmic trading.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {modules.map((mod) => (
                    <Link
                        key={mod.path}
                        to={mod.path}
                        className="block group"
                    >
                        <div className="h-full bg-slate-800 rounded-2xl p-6 border border-slate-700 transition-all duration-300 hover:border-slate-500 hover:shadow-xl hover:shadow-blue-900/20 hover:-translate-y-1">
                            <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-2xl mb-6 bg-gradient-to-br ${mod.color}`}>
                                <span className="drop-shadow-md">{mod.icon}</span>
                            </div>
                            <h2 className="text-xl font-bold text-white mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-blue-400 group-hover:to-emerald-400 transition-all">
                                {mod.title}
                            </h2>
                            <p className="text-slate-400 text-sm leading-relaxed">
                                {mod.description}
                            </p>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    );
}
