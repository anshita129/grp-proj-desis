import React from 'react';
import { Link } from "react-router-dom";

export default function HomePage() {
    const modules = [
        {
            title: "Learning",
            description: "Learn about algorithmic trading and financial markets through our interactive courses.",
            path: "/learning",
            color: "from-blue-500 to-cyan-400",
            shadow: "hover:shadow-[0_0_40px_rgba(59,130,246,0.3)] hover:border-blue-500/50",
            icon: "📚"
        },
        {
            title: "Trading",
            description: "Execute trades and manage your positions in real-time across various markets.",
            path: "/trading",
            color: "from-emerald-500 to-teal-400",
            shadow: "hover:shadow-[0_0_40px_rgba(16,185,129,0.3)] hover:border-emerald-500/50",
            icon: "📈"
        },
        {
            title: "Portfolio",
            description: "View your assets, track performance history, and analyze your current holdings.",
            path: "/portfolio",
            color: "from-purple-500 to-violet-400",
            shadow: "hover:shadow-[0_0_40px_rgba(168,85,247,0.3)] hover:border-purple-500/50",
            icon: "💼"
        },
        {
            title: "AI Agent",
            description: "Consult with our AI assistant for deep market insights and trading strategies.",
            path: "/ai",
            color: "from-amber-500 to-orange-400",
            shadow: "hover:shadow-[0_0_40px_rgba(245,158,11,0.3)] hover:border-amber-500/50",
            icon: "🤖"
        },
        {
            title: "Simulation",
            description: "Test your trading strategies in a gamified, risk-free market simulation environment.",
            path: "/simulation",
            color: "from-rose-500 to-pink-400",
            shadow: "hover:shadow-[0_0_40px_rgba(244,63,94,0.3)] hover:border-rose-500/50",
            icon: "🎮"
        }
    ];

    return (
        <div className="relative min-h-screen bg-slate-950 font-sans overflow-hidden selection:bg-indigo-500/30">
            {/* Animated Mesh Gradient Background Elements */}
            <div className="absolute top-0 -left-20 w-96 h-96 bg-indigo-600/20 rounded-full mix-blend-screen filter blur-[100px] animate-pulse"></div>
            <div className="absolute top-40 right-10 w-80 h-80 bg-emerald-600/10 rounded-full mix-blend-screen filter blur-[100px] animate-pulse" style={{ animationDelay: '2s' }}></div>
            <div className="absolute -bottom-20 left-1/3 w-[500px] h-[500px] bg-blue-600/10 rounded-full mix-blend-screen filter blur-[120px] animate-pulse" style={{ animationDelay: '4s' }}></div>

            <div className="relative z-10 p-8 max-w-7xl mx-auto pt-20">
                {/* Hero Section */}
                <div className="text-center mb-20 space-y-6">
                    <div className="inline-block mb-4 px-4 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 backdrop-blur-md">
                        <span className="text-sm font-semibold text-indigo-300 tracking-wider w-full uppercase">Next-Generation Platform</span>
                    </div>
                    <h1 className="text-6xl md:text-7xl font-extrabold text-white tracking-tight">
                        Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400">GRP DESIS</span>
                    </h1>
                    <p className="text-xl md:text-2xl text-slate-400 max-w-3xl mx-auto leading-relaxed mt-6">
                        Your complete ecosystem for learning, building, and deploying professional-grade algorithmic trading strategies.
                    </p>
                </div>

                {/* Dashboard Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 pb-20 relative z-20">
                    {modules.map((mod) => (
                        <Link
                            key={mod.path}
                            to={mod.path}
                            className="block group outline-none"
                        >
                            <div className={`h-full bg-slate-900/40 backdrop-blur-xl rounded-3xl p-8 border border-slate-800 transition-all duration-500 transform group-hover:-translate-y-2 ${mod.shadow} group-focus:ring-2 group-focus:ring-indigo-500`}>

                                <div className="flex items-center justify-between mb-8">
                                    <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl bg-gradient-to-br ${mod.color} shadow-lg relative`}>
                                        <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity rounded-2xl"></div>
                                        <span className="drop-shadow-md relative z-10">{mod.icon}</span>
                                    </div>
                                    <div className="w-10 h-10 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center group-hover:bg-slate-700 transition-colors">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-slate-400 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </div>
                                </div>

                                <h2 className="text-2xl font-bold text-slate-100 mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-blue-400 group-hover:to-emerald-400 transition-all">
                                    {mod.title}
                                </h2>
                                <p className="text-slate-400 text-base leading-relaxed">
                                    {mod.description}
                                </p>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
}
