from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import MicrodotSerializer


class MicrodotView(APIView):
    def post(self, request):
        serializer = MicrodotSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response('ok', status=status.HTTP_201_CREATED)
