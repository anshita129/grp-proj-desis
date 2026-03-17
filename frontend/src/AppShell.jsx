import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./modules/users/auth/AuthContext";

function AppShell() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    const navItems = [
        { name: "Home", path: "/" },
        { name: "Learning", path: "/learning" },
        { name: "Trading", path: "/trading" },
        { name: "Portfolio", path: "/portfolio" },
        { name: "AI Agent", path: "/ai" },
        { name: "Simulation", path: "/simulation" },
    ];

    return (
        <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
            {/* Sidebar Navigation */}
            <nav className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
                <div className="p-6 border-b border-slate-700">
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                        GRP DESIS
                    </h1>
                    <p className="text-sm text-slate-400 mt-1">Trading & Learning Platform</p>
                </div>

                <div className="flex flex-col flex-grow py-4">
                    {navItems.map((item) => {
                        // Determine active state - simple exact match for root, prefix match for others
                        const isActive = item.path === "/"
                            ? location.pathname === "/"
                            : location.pathname.startsWith(item.path);

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`px-6 py-3 text-sm font-medium transition-colors ${isActive
                                        ? "bg-blue-900/30 text-blue-400 border-r-4 border-blue-500"
                                        : "text-slate-300 hover:bg-slate-700 hover:text-white"
                                    }`}
                            >
                                {item.name}
                            </Link>
                        );
                    })}
                </div>

                <div className="p-4 border-t border-slate-700 text-xs text-center text-slate-500">
                    {user?.email ? `Signed in as ${user.email}` : "Signed in"}
                    <button
                        type="button"
                        onClick={async () => {
                            await logout();
                            navigate("/login");
                        }}
                        className="block w-full mt-2 text-blue-400 hover:text-blue-300"
                    >
                        Sign out
                    </button>
                </div>
            </nav>

            {/* Main Content Area */}
            <main className="flex-1 overflow-auto bg-slate-950">
                <Outlet />
            </main>
        </div>
    );
}

export default AppShell;
