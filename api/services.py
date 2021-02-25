import re
import requests

def github_api_fetch(url, auth_token):
    '''
    Fetch github traffic data given a url and authorization token with push access
    Returns a JSON object with the data or the error
    '''
    regex = r'^(?:https?:\/\/github\.com\/)([a-zA-Z0-9-_]+)(?:\/)([a-zA-Z0-9-_]+)(?:\/?)$'
    owner, repo_name = re.match(regex, url).group(1, 2)
    github_data = requests.get(
                    'https://api.github.com/repos/{}/{}/traffic/views'.format(owner, repo_name),
                    headers={"Authorization":"Token {}".format(str(auth_token))})
    return github_data.json()