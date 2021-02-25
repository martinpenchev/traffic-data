from datetime import datetime

from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from api.models import Repository, TrafficEvent
from .forms import UserForm

def home_page(request):
    if request.method == 'POST':
        response = redirect('/users/{}/repos'.format(str(request.POST['token'])))
        return response
    form = UserForm()
    return render(request, 'users/home.html', {'form': form})

@require_GET
def repo_detail(request, token, repository_id):
    if request.method == 'GET':
        try:
            user = get_user_model().objects.get(token=str(token))
            repository = Repository.objects.get(user=user, repository_id=int(repository_id))
            url_params = {'token':token,'repository_id':repository_id}

            mapping = {'start': 'timestamp__gte', 'end': 'timestamp__lte'}
            params = {mapping.get(name): value for name, value in request.GET.items() if (name == 'start' or name == 'end') and value != ""}
            # Check for valid data input
            if params != {}:
                for _, param in params.items():
                    try:
                        if param != datetime.strptime(param, "%Y-%m-%d").strftime("%Y-%m-%d"):
                            return render(request, 'users/repo_detail.html', {'error':'Please provide a YYYY-MM-DD date', **url_params})
                    except ValueError:
                        return render(request, 'users/repo_detail.html', {'error':'Please provide a YYYY-MM-DD date', **url_params})

            traffic = TrafficEvent.objects.filter(repository=repository, **params)
            labels = [event.timestamp.strftime("%Y-%m-%d") for event in traffic]
            counts = [int(event.count) for event in traffic]
            context = {
                'traffic':traffic,
                'labels':labels,
                'counts':counts,
                **url_params
            }
            return render(request, 'users/repo_detail.html', context)
        except ObjectDoesNotExist:
            return render(request, 'users/repo_detail.html', {'error':'Please provide a valid token and repository!'})

@require_GET
def repo_list(request, token):
    if request.method == 'GET':
        try:
            user = get_user_model().objects.get(token=str(token))
            mapping = {'start': 'created_at__gte', 'end': 'created_at__lte'}
            params = {mapping.get(name): value for name, value in request.GET.items() if (name == 'start' or name == 'end') and value != ""}
            
            # Check for valid data input
            if params != {}:
                for _, param in params.items():
                    try:
                        if param != datetime.strptime(param, "%Y-%m-%d").strftime("%Y-%m-%d"):
                            return render(request, 'users/repo_list.html', {'error':'Please provide a YYYY-MM-DD date', 'token':str(token)})
                    except ValueError:
                        return render(request, 'users/repo_list.html', {'error':'Please provide a YYYY-MM-DD date', 'token':str(token)})
            
            repositories = Repository.objects.filter(user=user, **params)
            return render(request, 'users/repo_list.html', {'repositories':repositories, 'token':str(token)})
        except ObjectDoesNotExist:
            return render(request, 'users/repo_list.html', {'error':'Please provide a valid token!', 'token':str(token)})