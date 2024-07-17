import os
import re
import requests
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
import html
import logging

logger = logging.getLogger('mkdocs.plugins.issues')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

class Issues(BasePlugin):
    config_scheme = (
        ('github_base_url', config_options.Type(str, required=True)),
        ('github_api_url', config_options.Type(str, required=True)),
        ('github_token', config_options.Type(str, default='')),
    )

    def on_config(self, config, **kwargs):
        logger.debug("Initializing Issues Plugin")
        github_token = self.config['github_token']
        if github_token.startswith('$'):
            env_var = github_token[1:]
            self.config['github_token'] = os.getenv(env_var, '')
            if not self.config['github_token']:
                logger.warning(f"Environment variable {env_var} is not set or empty.")

    def on_page_markdown(self, markdown, **kwargs):
        base_url = self.config['github_base_url']
        api_url = self.config['github_api_url']
        token = self.config.get('github_token', '')
        headers = {'Authorization': f'token {token}'} if token else {}
        issue_pattern = re.compile(rf'{re.escape(base_url)}/([^/]+)/([^/]+)/issues/(\d+)')
        logger.debug(f"Regex pattern: {issue_pattern.pattern}")

        def fetch_issue_status(owner, repo, issue_number):
            url = f"{api_url}/repos/{owner}/{repo}/issues/{issue_number}"
            logger.debug(f"Fetching issue from URL: {url}")
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching issue {owner}/{repo}#{issue_number}: {e}")
                return 'unknown', []

            issue = response.json()
            status = issue.get('state', 'unknown')
            labels = [
                {'name': label['name'], 'color': label['color']}
                for label in issue.get('labels', [])
            ]
            return status, labels

        matches = issue_pattern.finditer(markdown)
        found_any_matches = False
        for match in matches:
            found_any_matches = True
            logger.debug(f"Found match: {match.group()}")
            owner, repo, issue_number = match.groups()
            logger.debug(f"Processing issue: {owner}/{repo}#{issue_number}")
            status, labels = fetch_issue_status(owner, repo, issue_number)
            status_icon = '🟢' if status == 'open' else '🟣'
            status_title = 'Open' if status == 'open' else 'Closed'
            labels_str = ''.join(
                f'<span style="background-color: #{label["color"]}; color: #fff; padding: 1px 4px; border-radius: 3px; margin-left: 4px;">{html.escape(label["name"])}</span>'
                for label in labels
            ) or 'No labels'

            issue_info = f'<span title="{status_title}">{status_icon}</span> [{owner}/{repo}#{issue_number}]({match.group(0)}) {labels_str}'
            markdown = markdown.replace(match.group(0), issue_info)
            logger.debug(f"Processed issue: {owner}/{repo}#{issue_number} with status: {status}")

        if not found_any_matches:
            logger.debug("No matches found in the markdown content.")

        return markdown

# Setup function for entry point
def get_status():
    return Issues

