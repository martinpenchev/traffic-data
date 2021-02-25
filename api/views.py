from uuid import uuid4

from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import validate_email

# Authetication
from rest_framework.permissions import AllowAny
from .permissions import HasToken

# Models
from django.contrib.auth import get_user_model
from .models import Repository, TrafficEvent

# Github fetch service
from .services import github_api_fetch

class UserCreate(APIView):

    class InputSerializer(serializers.Serializer):
        email = serializers.EmailField(required=True)

        def create(self, validated_data):
            validated_data['token'] = uuid4()
            instance = get_user_model()(**validated_data)
            if validated_data['email'] is not None:
                instance.set_password(validated_data['email'])
            instance.save()
            return instance

    permission_classes = (AllowAny,)
    serializer_class = InputSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.InputSerializer(data=request.data)
        if serializer.is_valid():

            if get_user_model().objects.filter(email=serializer.validated_data['email']).exists():
                return Response({"error" : "This email already exists!"}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            token = get_user_model().objects.filter(email=serializer.validated_data['email']).values('token').get()
            return Response(token, status=status.HTTP_200_OK)

        error_message = ". ".join([str(error) for _, value in serializer.errors.items() for error in value])
        return Response({"error" : error_message}, status=status.HTTP_400_BAD_REQUEST)

class RepoList(APIView):

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Repository
            fields = ('repository_id', 'url', 'created_at',)

    permission_classes = (HasToken,)

    def get(self, request):
        token = request.META.get('HTTP_X_API_TOKEN')
        user = get_user_model().objects.get(token=token)
        query = Repository.objects.filter(user=user)

        if query.exists():
            data = self.OutputSerializer(query, many=True).data
            return Response(data, status=status.HTTP_200_OK)

        return Response({"error": "No repositories for {}".format(user)}, status=status.HTTP_400_BAD_REQUEST)

class RepoCreate(APIView):

    class InputSerializer(serializers.Serializer):
        url = serializers.URLField()
        auth_token = serializers.CharField(max_length=128)

        def create(self, validated_data):
            instance = Repository(**validated_data)
            instance.save()
            return instance
        
    serializer_class = InputSerializer
    permission_classes = (HasToken,)

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        if serializer.is_valid():
            token = request.META.get('HTTP_X_API_TOKEN')
            user = get_user_model().objects.get(token=str(token))
            url = serializer.validated_data.get('url')
            auth_token = serializer.validated_data.get('auth_token')

            # Check for duplicate repository
            if Repository.objects.filter(url=url).exists():
                return Response({"error":"The repository already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch initial data
            traffic_data = github_api_fetch(url, auth_token)

            # Check for github api errors
            if 'message' in traffic_data:
                return Response({"error" : traffic_data['message']}, status=status.HTTP_400_BAD_REQUEST)

            # Save repository data
            serializer.save(user=user)
            repository_id = Repository.objects.filter(url=serializer.validated_data.get('url')).values('repository_id')[0]['repository_id']

            # Store initial traffic data
            for traffic_event in traffic_data['views']:
                model = TrafficEvent()
                repo_obj = Repository.objects.get(repository_id=repository_id)
                model.repository = repo_obj
                model.timestamp = traffic_event['timestamp']
                model.count = traffic_event['count']
                model.uniques = traffic_event['uniques']
                model.save()
            
            return Response({'id': repository_id}, status=status.HTTP_200_OK)

        error_message = ". ".join(["{}: {}".format(str(key), str(error)) for key, value in serializer.errors.items() for error in value])
        return Response({"error" : error_message}, status=status.HTTP_400_BAD_REQUEST)

class RepoDetail(APIView):

    class OutputSerializer(serializers.ModelSerializer):
        traffic = serializers.StringRelatedField(many=True)
        class Meta:
            model = Repository
            fields = ('repository_id', 'url', 'created_at','traffic')

    permission_classes = (HasToken,)

    def get(self, request, *args, **kwargs):
        repository_id = kwargs.get('repository_id')
        token = request.META.get('HTTP_X_API_TOKEN')
        user = get_user_model().objects.get(token=str(token))

        try:
            instance = Repository.objects.get(repository_id=repository_id, user=user)
            data = self.OutputSerializer(instance).data
            return Response(data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"error":"There is no such repository for this user!"}, status=status.HTTP_400_BAD_REQUEST)


class RepoDelete(APIView):

    permission_classes = (HasToken,)

    def delete(self, request, *args, **kwargs):
        repository_id = kwargs.get('repository_id')
        token = request.META.get('HTTP_X_API_TOKEN')
        user = get_user_model().objects.get(token=str(token))
        try:
            instance = Repository.objects.get(repository_id=repository_id, user=user)
            instance.delete()
            return Response(status=status.HTTP_202_ACCEPTED)
        except ObjectDoesNotExist:
            return Response({"error":"There is no such repository for this user!"}, status=status.HTTP_400_BAD_REQUEST)
