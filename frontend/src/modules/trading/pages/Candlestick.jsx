import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";

export default function CandleChart({ symbol }) {
    const chartRef = useRef(null);
    const instanceRef = useRef(null);
    const [interval, setIntervalState] = useState("1m");

    const fetchCandles = async (ivl) => {
        try {
            const res = await fetch(`/api/trading/stocks/${symbol}/candles/?interval=${ivl}`);
            const data = await res.json();
            if (!data.data) return;

            const categoryData = [];
            const values = [];

            data.data.forEach(c => {
                categoryData.push(c.time);  // use raw ISO string
                console.log()
                values.push([
                    Number(c.open),
                    Number(c.close),
                    Number(c.low),
                    Number(c.high),
                ]);
            });

            const option = {
                backgroundColor: "#0f172a",
                tooltip: {
                    trigger: "axis",
                    formatter: (params) => {
                        const p = params[0];
                        if (!p) return "";
                        const [, o, c, l, h] = p.data;
                        const fmt = (n) => `₹${Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
                        const time = new Date(categoryData[p.dataIndex]).toLocaleString();
                        return `
                <div style="font-family: monospace; font-size: 12px;">
                    <b>${time}</b><br/>
                    Open: ${fmt(o)} &nbsp; Close: ${fmt(c)}<br/>
                    Low: ${fmt(l)} &nbsp; High: ${fmt(h)}
                </div>
            `;
                    }
                },
                xAxis: {
                    type: "category",
                    data: categoryData,
                    axisLabel: {
                        formatter: (val) => new Date(val).toLocaleTimeString("en-IN", {
                            hour: "2-digit", minute: "2-digit", hour12: false
                        }),
                        color: "#94a3b8",
                    },
                    axisLine: { lineStyle: { color: "#334155" } },
                },
                yAxis: {
                    scale: true,
                    axisLabel: {
                        formatter: (val) => `₹${val.toLocaleString("en-IN")}`,
                        color: "#94a3b8",
                    },
                    axisLine: { lineStyle: { color: "#334155" } },
                    splitLine: { lineStyle: { color: "#1e293b" } },
                },
                dataZoom: [
                    {
                        type: "inside",
                        start: 60, end: 100,
                        zoomOnMouseWheel: false,  // ← disable scroll zoom
                        moveOnMouseMove: true,
                    },
                    {
                        type: "slider", start: 60, end: 100, height: 20, bottom: 0,
                        borderColor: "#334155", fillerColor: "#1e293b44",
                        handleStyle: { color: "#6366f1" },
                        textStyle: { color: "#94a3b8" },
                    }
                ],
                series: [{
                    type: "candlestick",
                    data: values,
                    itemStyle: {
                        color: "#22c55e",
                        color0: "#ef4444",
                        borderColor: "#22c55e",
                        borderColor0: "#ef4444",
                    },
                }],
            };
            instanceRef.current?.setOption(option);
        } catch (e) {
            console.error("fetch error:", e);
        }
    };

    useEffect(() => {
        if (chartRef.current) {
            instanceRef.current = echarts.init(chartRef.current);
        }
        fetchCandles(interval);

        return () => instanceRef.current?.dispose();
    }, []);

    useEffect(() => {
        fetchCandles(interval);
    }, [interval, symbol]);

    useEffect(() => {
        const t = setInterval(() => fetchCandles(interval), 15000);
        return () => clearInterval(t);
    }, [interval, symbol]);


    useEffect(() => {
        const handleResize = () => instanceRef.current?.resize();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);


    return (
        <div className="space-y-3">
            <div className="flex gap-2">
                {["1m", "5m", "15m", "30m", "1h", "1d"].map(i => (
                    <button key={i} onClick={() => setIntervalState(i)}
                        className={`px-3 py-1 text-xs font-mono rounded transition-colors ${interval === i
                            ? "bg-indigo-500 text-white"
                            : "bg-slate-800 text-slate-400 hover:text-slate-200"
                            }`}
                    >
                        {i}
                    </button>
                ))}
            </div>

            <div
                ref={chartRef}
                style={{ height: 450, width: "100%" }}
                className="rounded-xl border border-slate-700"
            />
        </div>
    );
}