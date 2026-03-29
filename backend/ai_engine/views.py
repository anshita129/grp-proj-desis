from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

from .llm_service import get_chatbot_reply
from .models import AIInsight


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


@api_view(["POST"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    user = request.user
    user_message = (request.data.get("message") or "").strip()

    if not user_message:
        return Response({"reply": "Please enter a message."}, status=400)

    context = {
        "user_message": user_message,
        "user": user,
        "username": getattr(user, "username", ""),
    }

    reply = get_chatbot_reply(context)

    AIInsight.objects.create(
        user=user,
        summary=reply,
    )

    return Response({
        "reply": reply,
    })


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