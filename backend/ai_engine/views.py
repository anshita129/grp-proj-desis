from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .llm_service import get_chatbot_reply
from .models import AIInsight


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    user = request.user
    user_message = (request.data.get("message") or "").strip()

    if not user_message:
        return Response({"reply": "Please enter a message."}, status=400)

    # 🔥 Minimal context (NO ML, NO RULES)
    context = {
        "user_message": user_message,
        "user": user,
        "username": getattr(user, "username", ""),
    }

    reply = get_chatbot_reply(context)

    # Optional: save chat summary
    AIInsight.objects.create(
        user=user,
        
        summary=reply,
    )

    return Response({
        "reply": reply,
    })


# Optional: history API (cleaned)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ai_history(request):
    insights = AIInsight.objects.filter(user=request.user).order_by("-created_at")

    data = [
        {
            "id": i.id,
            "summary": i.summary,
            "created_at": i.created_at,
        }
        for i in insights
    ]

    return Response(data)