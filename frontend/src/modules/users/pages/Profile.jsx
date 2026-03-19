import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function Profile() {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetch("http://localhost:8000/api/users/profile/", {
            method: "GET",
            credentials: "include",
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Failed to fetch profile data");
                }
                return res.json();
            })
            .then((data) => {
                setUser(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error(err);
                setError("Could not load profile data.");
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="p-8 text-white min-h-screen bg-slate-950">
                Loading profile...
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 text-red-400 min-h-screen bg-slate-950">
                {error}
            </div>
        );
    }

    const recentActivities = user.recent_activity || [];

    return (
        <div className="p-8 text-white min-h-screen bg-slate-950">
            <h1 className="text-4xl font-bold mb-8">Profile</h1>

            <div className="max-w-6xl mx-auto space-y-6">

                <div className="bg-slate-800 rounded-2xl p-6 shadow-lg border border-slate-700">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                        <div className="flex items-center gap-5">
                            <div className="w-24 h-24 rounded-full bg-blue-500 flex items-center justify-center text-4xl font-bold shadow-md">
                                {user.name ? user.name[0].toUpperCase() : "U"}
                            </div>

                            <div>
                                <h2 className="text-3xl font-semibold">{user.name}</h2>
                                <p className="text-slate-400 text-lg">{user.email}</p>
                                <p className="text-sm text-slate-500 mt-1">
                                    Last login: {user.last_login || "Not available"}
                                </p>
                            </div>
                        </div>

                        <div className="flex flex-wrap gap-3">
                            <span className="px-4 py-2 rounded-full bg-blue-900/40 text-blue-300 text-sm font-medium">
                                {user.account_type}
                            </span>
                            <span className="px-4 py-2 rounded-full bg-emerald-900/40 text-emerald-300 text-sm font-medium">
                                {user.ai_usage_count} AI Insights
                            </span>
                            <span className="px-4 py-2 rounded-full bg-amber-900/40 text-amber-300 text-sm font-medium">
                                {user.risk_profile} Risk
                            </span>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    <div className="lg:col-span-2 space-y-6">

                        <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
                            <h3 className="text-xl font-semibold mb-4">Financial Summary</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="bg-slate-700 p-4 rounded-xl">
                                    <p className="text-sm text-slate-400">Portfolio Value</p>
                                    <p className="text-2xl font-bold mt-1">₹{user.portfolio_value}</p>
                                </div>
                                <div className="bg-slate-700 p-4 rounded-xl">
                                    <p className="text-sm text-slate-400">Available Balance</p>
                                    <p className="text-2xl font-bold mt-1">₹{user.available_balance}</p>
                                </div>
                                <div className="bg-slate-700 p-4 rounded-xl">
                                    <p className="text-sm text-slate-400">Holdings Count</p>
                                    <p className="text-2xl font-bold mt-1">{user.holdings_count}</p>
                                </div>
                                <div className="bg-slate-700 p-4 rounded-xl">
                                    <p className="text-sm text-slate-400">Member Since</p>
                                    <p className="text-2xl font-bold mt-1">{user.member_since}</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
                            <h3 className="text-xl font-semibold mb-4">Trading & AI Insights</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="bg-slate-700 p-4 rounded-xl">
                                    <p className="text-sm text-slate-400">Total Orders</p>
                                    <p className="text-lg font-medium mt-1">{user.total_orders}</p>
                                </div>
                                <div className="bg-slate-700 p-4 rounded-xl">
                                    <p className="text-sm text-slate-400">Buy Orders</p>
                                    <p className="text-lg font-medium mt-1">{user.buy_orders}</p>
                                </div>
                                <div className="bg-slate-700 p-4 rounded-xl">
                                    <p className="text-sm text-slate-400">Sell Orders</p>
                                    <p className="text-lg font-medium mt-1">{user.sell_orders}</p>
                                </div>
                                <div className="bg-slate-700 p-4 rounded-xl">
                                    <p className="text-sm text-slate-400">Trader Type</p>
                                    <p className="text-lg font-medium mt-1">{user.trader_type}</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
                            <h3 className="text-xl font-semibold mb-4">Recent Activity</h3>
                            <div className="space-y-3">
                                {recentActivities.length > 0 ? (
                                    recentActivities.map((activity, index) => (
                                        <div
                                            key={index}
                                            className="bg-slate-700 rounded-xl px-4 py-3 text-slate-200"
                                        >
                                            {activity}
                                        </div>
                                    ))
                                ) : (
                                    <div className="bg-slate-700 rounded-xl px-4 py-3 text-slate-400">
                                        No recent activity available.
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6">

                        <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
                            <h3 className="text-xl font-semibold mb-4">AI Summary</h3>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between gap-4">
                                    <span className="text-slate-400">Risk Profile</span>
                                    <span className="text-white">{user.risk_profile}</span>
                                </div>
                                <div className="flex justify-between gap-4">
                                    <span className="text-slate-400">Trader Type</span>
                                    <span className="text-white">{user.trader_type}</span>
                                </div>
                                <div className="flex justify-between gap-4">
                                    <span className="text-slate-400">Anomaly Detected</span>
                                    <span className="text-white">
                                        {user.anomaly_detected ? "Yes" : "No"}
                                    </span>
                                </div>
                            </div>

                            <div className="mt-4 bg-slate-700 rounded-xl p-4">
                                <p className="text-sm text-slate-400 mb-2">Latest AI Summary</p>
                                <p className="text-slate-200 text-sm">
                                    {user.ai_summary}
                                </p>
                            </div>
                        </div>

                        {/* <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
                            <h3 className="text-xl font-semibold mb-4">Account Preferences</h3>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-slate-400">Theme</span>
                                    <span className="text-white">Dark Mode</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-400">Notifications</span>
                                    <span className="text-white">Enabled</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-400">AI Suggestions</span>
                                    <span className="text-white">On</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-400">Account Type</span>
                                    <span className="text-white">{user.account_type}</span>
                                </div>
                            </div>
                        </div> */}

                        <div className="bg-slate-800 rounded-2xl p-6 border border-slate-700">
                            <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
                            <div className="space-y-3">
                                {/* <button
                                    onClick={() => navigate("/profile/edit")}
                                    className="w-full bg-blue-600 hover:bg-blue-500 transition-colors rounded-xl py-3 font-medium"
                                >
                                    Edit Profile
                                </button> */}

                                <button
                                    onClick={() => navigate("/portfolio")}
                                    className="w-full bg-slate-700 hover:bg-slate-600 transition-colors rounded-xl py-3 font-medium"
                                >
                                    View Portfolio
                                </button>

                                <button
                                    onClick={() => navigate("/ai")}
                                    className="w-full bg-slate-700 hover:bg-slate-600 transition-colors rounded-xl py-3 font-medium"
                                >
                                    Open AI Agent
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Profile;