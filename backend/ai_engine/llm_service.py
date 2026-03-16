import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def get_fallback_reply(context, user_message):
    msg = user_message.lower().strip()
    risk = context.get("risk_profile", "Unknown")
    ml = context.get("ml_based", {})
    tips = context.get("final_tips", [])

    trader = ml.get("trader_type") or "unavailable"
    anomaly = ml.get("is_anomaly")

    if msg in ["hi", "hello", "hey"]:
        return "Hello! Ask me about your risk profile, trader behavior, anomaly detection, or ways to improve."

    if "risk" in msg:
        return f"Your current risk profile is {risk}. This reflects your present trading and portfolio pattern."

    if "trader" in msg:
        return f"Your trader type is currently {trader}."

    if "anomaly" in msg:
        if anomaly is True:
            return "An unusual trading pattern was detected recently."
        if anomaly is False:
            return "No anomaly is currently detected in your trading behavior."
        return "Anomaly analysis is currently unavailable."

    if "improve" in msg or "suggest" in msg or "better" in msg:
        if tips:
            return "Here are some improvements:\n- " + "\n- ".join(tips[:3])
        return "Start with smaller trades, avoid risky decisions, and follow a consistent plan."

    return "I can help explain your risk profile, trader type, anomaly status, and suggestions based on your dashboard data."


def get_chatbot_reply(context):
    username = context.get("username", "user")
    risk_profile = context.get("risk_profile", "Unknown")
    final_tips = context.get("final_tips", [])
    ml_based = context.get("ml_based", {})
    user_message = context.get("user_message", "")

    trader_type = ml_based.get("trader_type", "Unavailable")
    anomaly_detected = ml_based.get("is_anomaly", False)

    system_prompt = f"""
You are an AI trading assistant for a student project.

Reply in simple English.
Keep replies short.
Use only the given data.
Do not invent facts.
If the message is a greeting, respond briefly.
If the user asks how to improve, use the tips.
If data is unavailable, say that clearly.

Context:
Username: {username}
Risk profile: {risk_profile}
Trader type: {trader_type}
Anomaly detected: {anomaly_detected}
Tips: {final_tips}
"""

    try:
        response = client.chat.completions.create(
            #model="openrouter/free",
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=120,
            extra_headers={
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "AI Trading Assistant Project",
            },
        )

        if not response or not response.choices:
            return get_fallback_reply(context, user_message)

        msg = response.choices[0].message
        content = msg.content if msg else None

        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("text"):
                    parts.append(item["text"])
                elif hasattr(item, "text") and item.text:
                    parts.append(item.text)

            joined = " ".join(parts).strip()
            if joined:
                return joined

        return get_fallback_reply(context, user_message)

    except Exception as e:
        print("LLM ERROR:", str(e))
        return get_fallback_reply(context, user_message)