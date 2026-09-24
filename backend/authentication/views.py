from django.shortcuts import render
from rest_framework.views import APIView
from .models import CustomUser, SingUpCode, TempUser
from .serilaizers import TempUserCreateSerializer, VerifyCodeSerializer
from rest_framework.response import Response


class TempUserCreateAPIView(APIView):
    def post(self, request):
        serializer = TempUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            "message": "Code sent to the email",
            "data": serializer.data
        })
        

class VerifyCodeAPIView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)
    
