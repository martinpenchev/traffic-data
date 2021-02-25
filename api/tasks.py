from __future__ import absolute_import
from celery import shared_task
from .models import Repository, TrafficEvent

def github_api_fetch(url, auth_token):
    regex = r'^(?:https?:\/\/github\.com\/)([a-zA-Z0-9-_]+)(?:\/)([a-zA-Z0-9-_]+)(?:\/?)$'
    owner, repo_name = re.match(regex, url).group(1, 2)
    github_data = requests.get(
                    'https://api.github.com/repos/{}/{}/traffic/views'.format(owner, repo_name),
                    headers={"Authorization":"Token {}".format(str(auth_token))})
    return github_data.json()

# Fetch GITHUB api daily
@shared_task()
def get_traffic_data():
    for repository in Repository.objects.all():
        url = repository.url
        auth_token = repository.auth_token
        data = github_api_fetch(url, auth_token)

        for traffic_event in data['views']:
            model = TrafficEvent()
            repo_obj = Repository.objects.get(repository_id=repository.repository_id)

            # Check if event already exists
            if TrafficEvent.objects.get(timestamp=traffic_event['timestamp']).exists() == False:
                model.repository = repo_obj
                model.timestamp = traffic_event['timestamp']
                model.count = traffic_event['count']
                model.uniques = traffic_event['uniques']
                model.save()

