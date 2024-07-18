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
        ('configs', config_options.Type(list, required=True)),
    )

    def on_config(self, config, **kwargs):
        logger.debug("Initializing Issues Plugin")
        for conf in self.config['configs']:
            token = conf['token']
            if token.startswith('$'):
                env_var = token[1:]
                conf['token'] = os.getenv(env_var, '')
                if not conf['token']:
                    logger.warning(f"Environment variable {env_var} is not set or empty.")

    def on_page_markdown(self, markdown, **kwargs):
        logger.debug("Processing page markdown")
        for conf in self.config['configs']:
            service = conf['service']
            base_url = conf['base_url']
            api_url = conf['api_url']
            token = conf['token']
            headers = {'Authorization': f'token {token}'} if token else {}
            if service == 'gitlab':
                headers = {'Private-Token': token} if token else {}

            issue_pattern = re.compile(rf'{re.escape(base_url)}/([^/]+)/([^/]+)/issues/(\d+)' if service == 'github' else rf'{re.escape(base_url)}/([^/]+)/([^/]+)/-/issues/(\d+)')
            logger.debug(f"Regex pattern for {base_url}: {issue_pattern.pattern}")

            def fetch_issue_status(owner, repo, issue_number):
                if service == 'github':
                    url = f"{api_url}/repos/{owner}/{repo}/issues/{issue_number}"
                elif service == 'gitlab':
                    repo_encoded = f"{owner}%2F{repo}"
                    url = f"{api_url}/projects/{repo_encoded}/issues/{issue_number}"

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
                    {'name': label['name'], 'color': label['color'] if service == 'github' else '007BFF'}
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

                if service == 'github':
                    issue_info = f'<span title="{status_title}">{status_icon}</span> [{owner}/{repo}#{issue_number}]({match.group(0)}) {labels_str}'
                elif service == 'gitlab':
                    issue_info = f'<span title="{status_title}">{status_icon}</span> [{owner}/{repo}#{issue_number}]({match.group(0).replace("/-/issues/", "/issues/")}) {labels_str}'

                markdown = markdown.replace(match.group(0), issue_info)
                logger.debug(f"Processed issue: {owner}/{repo}#{issue_number} with status: {status}")

            if not found_any_matches:
                logger.debug(f"No matches found in the markdown content for base URL: {base_url}")

        return markdown

# Setup function for entry point
def get_status():
    return Issues

