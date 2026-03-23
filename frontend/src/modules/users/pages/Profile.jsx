import { useEffect, useState } from "react";

function Profile({ show, onClose }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!show) return;

        setLoading(true);
        setError("");

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
    }, [show]);

    if (!show) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
            <div className="w-full max-w-2xl rounded-3xl bg-[#08133b] border border-blue-900/60 shadow-2xl overflow-hidden">
                <div className="flex items-center justify-between px-6 py-4 border-b border-blue-900/60">
                    <h2 className="text-xl font-semibold text-white">Profile 👤</h2>

                    <button
                        onClick={onClose}
                        className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 transition text-slate-200"
                    >
                        ✖
                    </button>
                </div>

                <div className="p-6 text-white">
                    {loading ? (
                        <div className="text-slate-300">Loading profile...</div>
                    ) : error ? (
                        <div className="text-red-400">{error}</div>
                    ) : user ? (
                        <div className="space-y-6">
                            <div className="flex items-center gap-4">
                                <div className="w-16 h-16 rounded-full bg-blue-500 flex items-center justify-center text-2xl font-bold text-white shadow-md">
                                    {user.name ? user.name[0].toUpperCase() : "U"}
                                </div>

                                <div>
                                    <h3 className="text-2xl font-semibold">{user.name}</h3>
                                    <p className="text-slate-400">{user.email}</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-[#101a43] border border-blue-900/70 p-4 rounded-2xl">
                                    <p className="text-sm text-slate-400">Portfolio</p>
                                    <p className="text-lg font-semibold mt-1">
                                        ₹{user.portfolio_value}
                                    </p>
                                </div>

                                <div className="bg-[#101a43] border border-blue-900/70 p-4 rounded-2xl">
                                    <p className="text-sm text-slate-400">Balance</p>
                                    <p className="text-lg font-semibold mt-1">
                                        ₹{user.available_balance}
                                    </p>
                                </div>

                                <div className="bg-[#101a43] border border-blue-900/70 p-4 rounded-2xl">
                                    <p className="text-sm text-slate-400">Holdings</p>
                                    <p className="text-lg font-semibold mt-1">
                                        {user.holdings_count}
                                    </p>
                                </div>

                                <div className="bg-[#101a43] border border-blue-900/70 p-4 rounded-2xl">
                                    <p className="text-sm text-slate-400">Member Since</p>
                                    <p className="text-lg font-semibold mt-1">
                                        {user.member_since}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-slate-300">No profile data found.</div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Profile;