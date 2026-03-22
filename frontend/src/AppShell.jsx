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
            <nav className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
                <div className="p-6 border-b border-slate-700">
                    <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                        GRP DESIS
                    </h1>
                    <p className="text-sm text-slate-400 mt-1">Trading & Learning Platform</p>
                </div>

                <div className="flex flex-col flex-grow py-4">
                    {navItems.map((item) => {
                        const isActive = item.path === "/"
                            ? location.pathname === "/"
                            : location.pathname.startsWith(item.path);

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`px-6 py-3 text-sm font-medium transition-colors ${
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

                <div className="p-4 border-t border-slate-700 text-center">
                    <Link
                        to="/profile"
                        className="flex items-center justify-center gap-3 p-3 rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors"
                    >
                        <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                            {user?.username ? user.username[0].toUpperCase() : "U"}
                        </div>
                        <div className="text-left">
                            <p className="text-sm font-medium text-white">
                                {user?.username || "User"}
                            </p>
                            <p className="text-xs text-slate-400">
                                {user?.email || "View Profile"}
                            </p>
                        </div>
                    </Link>

                    <button
                        type="button"
                        onClick={async () => {
                            await logout();
                            navigate("/login");
                        }}
                        className="block w-full mt-3 text-sm text-blue-400 hover:text-blue-300"
                    >
                        Sign out
                    </button>
                </div>
            </nav>

            <main className="flex-1 overflow-auto bg-slate-950">
                <Outlet />
            </main>
        </div>
    );
}

export default AppShell;