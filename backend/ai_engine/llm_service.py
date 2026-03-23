import os
import traceback
from google import genai
from .peer_analytics import get_peer_summary


def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    print("GEMINI API KEY PRESENT:", bool(api_key))
    return genai.Client(api_key=api_key)


def clean_text(x):
    if not x:
        return ""
    x = x.replace("**", "")
    x = x.replace("__", "")
    x = x.replace("–", "-")
    return x.strip()


def get_fallback_reply(context, user_message, reason="unknown"):
    print(f"USING FALLBACK: {reason}")

    msg = user_message.lower().strip()
    ml = context.get("ml_based", {})
    risk = context.get("risk_profile", "Unknown")
    trader = ml.get("trader_type") or "unavailable"
    anomaly = ml.get("is_anomaly")

    peer = context.get("peer_data", {})
    us = peer.get("user_stats", {})
    ps = peer.get("peer_summary", {})
    tips = peer.get("peer_generated_tips", [])

    if msg in ["hi", "hello", "hey"]:
        return "Hi! Ask me about your trading profile, peer comparison, or how to improve."

    if "risk" in msg:
        return f"Your current risk profile is {risk}."

    if "trader" in msg:
        return f"Your trader type is currently {trader}."

    if "anomaly" in msg:
        if anomaly is True:
            return "An unusual trading pattern was detected recently."
        if anomaly is False:
            return "No anomaly is currently detected in your trading behavior."
        return "Anomaly analysis is currently unavailable."

    if "improve" in msg or "better" in msg or "suggest" in msg:
        ans = []
        if us and ps:
            ans.append("Comparison with peers:")
            ans.append(
                f"- You have {us.get('total_trades', 0)} trades, while peer average is {ps.get('avg_total_trades', 0)}."
            )
            ans.append(
                f"- Your portfolio diversity is {us.get('portfolio_diversity', 0)}, while peer average is {ps.get('avg_portfolio_diversity', 0)}."
            )
            ans.append("")
            ans.append("How to improve:")
        for t in tips[:3]:
            ans.append(f"- {t}")
        if ans:
            return "\n".join(ans)
        return "Try using smaller trade sizes, maintaining diversification, and avoiding unnecessary trades."

    return "I can explain your profile, anomaly status, peer comparison, and improvement suggestions."


def get_chatbot_reply(context):
    username = context.get("username", "user")
    risk_profile = context.get("risk_profile", "Unknown")
    final_tips = context.get("final_tips", [])
    ml_based = context.get("ml_based", {})
    user_message = context.get("user_message", "")
    user = context.get("user")

    trader_type = ml_based.get("trader_type", "Unavailable")
    anomaly_detected = ml_based.get("is_anomaly", False)

    peer_data = {}
    if user is not None:
        peer_data = get_peer_summary(
            user=user,
            risk_profile=risk_profile,
            trader_type=trader_type,
        )

    context["peer_data"] = peer_data

    user_stats = peer_data.get("user_stats", {})
    peer_summary = peer_data.get("peer_summary", {})
    comparison_points = peer_data.get("comparison_points", [])
    peer_generated_tips = peer_data.get("peer_generated_tips", [])
    peer_user_count = peer_summary.get("peer_user_count", 0)

    merged_tips = list(final_tips or [])
    for t in peer_generated_tips:
        if t not in merged_tips:
            merged_tips.append(t)

    system_prompt = f"""
You are an AI trading assistant for a student project.

Rules:
- Reply in simple English.
- Use plain text only.
- Do not use markdown.
- Be clear and useful.
- Answer what is being asked.

- If the user message is a greeting, respond briefly and do not give analysis.
- Keep the answer moderately detailed.

- Use only the provided data.
- You can use facts from internet.
- Do not mention any individual other user.
- Use peer data only in aggregated form.

Available data:
Username: {username}
Risk profile: {risk_profile}
Trader type: {trader_type}
Anomaly detected: {anomaly_detected}
Current user stats: {user_stats}
Peer summary: {peer_summary}
Comparison points: {comparison_points}
Tips: {merged_tips[:4]}
Peer users considered: {peer_user_count}
""".strip()

    try:
        client = get_client()

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                system_prompt,
                f"User question: {user_message}"
            ],
        )

        print("RAW GEMINI RESPONSE:", response)

        text = clean_text(getattr(response, "text", ""))

        if text:
            print("LLM SUCCESS: Gemini returned text")
            return text

        return get_fallback_reply(context, user_message, "empty Gemini text")

    except Exception as e:
        print("GEMINI ERROR:", repr(e))
        traceback.print_exc()
        return get_fallback_reply(context, user_message, f"exception: {repr(e)}")