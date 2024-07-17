import re
import os
import re
import requests
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
import html

class Issues(BasePlugin):
    config_scheme = (
        ('github_base_url', config_options.Type(str, required=True)),
        ('github_api_url', config_options.Type(str, required=True)),
        ('github_token', config_options.Type(str, default='')),
    )

    def on_config(self, config, **kwargs):
        github_token = self.config['github_token']
        if github_token.startswith('$'):
            env_var = github_token[1:]
            self.config['github_token'] = os.getenv(env_var, '')

    def on_page_markdown(self, markdown, **kwargs):
        base_url = self.config['github_base_url']
        api_url = self.config['github_api_url']
        token = self.config.get('github_token', '')
        headers = {'Authorization': f'token {token}'} if token else {}
        issue_pattern = re.compile(rf'{re.escape(base_url)}/([^/]+)/([^/]+)/issues/(\d+)')

        def fetch_issue_status(owner, repo, issue_number):
            url = f"{api_url}/repos/{owner}/{repo}/issues/{issue_number}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                issue = response.json()
                status = issue.get('state', 'unknown')
                labels = [
                    {'name': label['name'], 'color': label['color']}
                    for label in issue.get('labels', [])
                ]
                return status, labels
            else:
                return 'unknown', []

        matches = issue_pattern.finditer(markdown)
        for match in matches:
            owner, repo, issue_number = match.groups()
            status, labels = fetch_issue_status(owner, repo, issue_number)
            status_icon = '🟢' if status == 'open' else '🟣'
            labels_str = ''.join(
                f'<span style="background-color: #{label["color"]}; color: #fff; padding: 1px 4px; border-radius: 3px; margin-left: 4px;">{html.escape(label["name"])}</span>'
                for label in labels
            ) or 'No labels'

            issue_info = f"{status_icon} [{match.group(0)}] {labels_str}"
            markdown = markdown.replace(match.group(0), issue_info)

        return markdown

# Setup function for entry point
def get_status():
    return Issues

