import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "./modules/users/auth/AuthContext";
import Profile from "./modules/users/pages/Profile";

function AppShell() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [showProfile, setShowProfile] = useState(false);

    const navItems = [
        { name: "Home", path: "/" },
        { name: "Learning", path: "/learning" },
        { name: "Trading", path: "/trading" },
        { name: "Portfolio", path: "/portfolio" },
        { name: "AI Agent", path: "/ai" },
        { name: "Simulation", path: "/simulation" },
    ];

    return (
        <>
            <div className="flex flex-col h-screen bg-slate-900 text-slate-100 font-sans">
                {/* Top Navbar */}
                <header className="h-16 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-6 shrink-0">
                    <div className="flex items-center gap-6">
                        <button
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                            className="p-2 -ml-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                            aria-label="Toggle Sidebar"
                        >
                            {isSidebarOpen ? (
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            ) : (
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            )}
                        </button>

                        <div>
                            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 whitespace-nowrap">
                                EduTrade
                            </h1>
                        </div>

                        {/* Top nav links */}
                        <div className="hidden lg:flex ml-4 gap-1">
                            {navItems.map((item) => {
                                const isActive = item.path === "/"
                                    ? location.pathname === "/"
                                    : location.pathname.startsWith(item.path);

                                return (
                                    <Link
                                        key={item.path}
                                        to={item.path}
                                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                                            isActive
                                                ? "bg-blue-900/30 text-blue-400 font-semibold"
                                                : "text-slate-300 hover:bg-slate-700 hover:text-white"
                                        }`}
                                    >
                                        {item.name}
                                    </Link>
                                );
                            })}
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden sm:flex flex-col items-end">
                            <span className="text-sm font-medium text-white">{user?.username || "User"}</span>
                            <span className="text-xs text-slate-400">{user?.email || ""}</span>
                        </div>

                        <button
                            type="button"
                            onClick={() => setShowProfile(true)}
                            className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-sm hover:ring-2 ring-blue-400 transition-all cursor-pointer"
                        >
                            {user?.username ? user.username[0].toUpperCase() : "U"}
                        </button>

                        <div className="w-px h-6 bg-slate-700 mx-2 hidden sm:block"></div>

                        <button
                            onClick={async () => {
                                await logout();
                                navigate("/login");
                            }}
                            className="text-sm font-medium text-slate-400 hover:text-white transition-colors"
                        >
                            Sign out
                        </button>
                    </div>
                </header>

                <div className="flex flex-1 overflow-hidden relative">
                    {/* Collapsible Sidebar */}
                    <div
                        className={`transition-all duration-300 ease-in-out ${
                            isSidebarOpen ? "w-64 opacity-100" : "w-0 opacity-0 lg:opacity-100 lg:w-0"
                        } overflow-hidden shrink-0 bg-slate-800 border-r border-slate-700 flex flex-col z-20 absolute lg:relative h-full shadow-2xl lg:shadow-none`}
                    >
                        <div className="flex flex-col flex-grow py-4 w-64 min-w-[16rem]">
                            <div className="px-6 pb-4 border-b border-slate-700 mb-4 lg:hidden">
                                <p className="text-sm text-slate-400">Navigation</p>
                            </div>

                            {navItems.map((item) => {
                                const isActive = item.path === "/"
                                    ? location.pathname === "/"
                                    : location.pathname.startsWith(item.path);

                                return (
                                    <Link
                                        key={item.path}
                                        to={item.path}
                                        onClick={() => {
                                            if (window.innerWidth < 1024) setIsSidebarOpen(false);
                                        }}
                                        className={`px-6 py-3 text-sm font-medium transition-colors w-full flex items-center ${
                                            isActive
                                                ? "bg-blue-900/30 text-blue-400 border-r-4 border-blue-500"
                                                : "text-slate-300 hover:bg-slate-700 hover:text-white"
                                        }`}
                                    >
                                        {item.name}
                                    </Link>
                                );
                            })}
                        </div>
                    </div>

                    {/* Mobile overlay backdrop */}
                    {isSidebarOpen && (
                        <div
                            className="fixed inset-0 bg-black/50 z-10 lg:hidden"
                            onClick={() => setIsSidebarOpen(false)}
                        />
                    )}

                    {/* Main Content */}
                    <main className="flex-1 overflow-auto bg-slate-950 w-full relative z-0 rounded-tl-lg shadow-inner">
                        <Outlet />
                    </main>
                </div>
            </div>

            <Profile
                show={showProfile}
                onClose={() => setShowProfile(false)}
            />
        </>
    );
}

export default AppShell;