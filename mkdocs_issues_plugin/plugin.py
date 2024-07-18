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
            pr_pattern = re.compile(rf'{re.escape(base_url)}/([^/]+)/([^/]+)/pull/(\d+)' if service == 'github' else rf'{re.escape(base_url)}/([^/]+)/([^/]+)/-/merge_requests/(\d+)')
            logger.debug(f"Issue regex pattern for {base_url}: {issue_pattern.pattern}")
            logger.debug(f"PR regex pattern for {base_url}: {pr_pattern.pattern}")

            def fetch_issue_status(owner, repo, number):
                if service == 'github':
                    url = f"{api_url}/repos/{owner}/{repo}/issues/{number}"
                elif service == 'gitlab':
                    repo_encoded = f"{owner}%2F{repo}"
                    url = f"{api_url}/projects/{repo_encoded}/issues/{number}"

                logger.debug(f"Fetching issue from URL: {url}")
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching issue {owner}/{repo}#{number}: {e}")
                    return 'unknown', []

                issue = response.json()
                status = issue.get('state', 'unknown')
                labels = [
                    {'name': label['name'], 'color': label['color'] if service == 'github' else '007BFF'}
                    for label in issue.get('labels', [])
                ]
                return status, labels

            def fetch_pr_status(owner, repo, number):
                if service == 'github':
                    url = f"{api_url}/repos/{owner}/{repo}/pulls/{number}"
                elif service == 'gitlab':
                    repo_encoded = f"{owner}%2F{repo}"
                    url = f"{api_url}/projects/{repo_encoded}/merge_requests/{number}"

                logger.debug(f"Fetching PR from URL: {url}")
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching PR {owner}/{repo}#{number}: {e}")
                    return 'unknown', []

                pr = response.json()
                status = pr.get('state', 'unknown')
                if service == 'github':
                    merged = pr.get('merged_at', None) is not None
                    if merged:
                        status = 'merged'
                    elif status == 'closed':
                        status = 'closed'
                elif service == 'gitlab':
                    if pr.get('merged_at', False):
                        status = 'merged'
                    elif pr['state'] == 'closed':
                        status = 'closed'
                labels = []
                return status, labels

            def process_matches(pattern, fetch_status_fn, icon_map, link_suffix_transform_fn=None):
                nonlocal markdown
                matches = pattern.finditer(markdown)
                for match in matches:
                    owner, repo, number = match.groups()
                    logger.debug(f"Processing {fetch_status_fn.__name__.split('_')[1]}: {owner}/{repo}#{number}")
                    status, labels = fetch_status_fn(owner, repo, number)
                    status_icon = icon_map.get(status, '🔴')
                    status_title = status.capitalize() if status in icon_map else 'Closed'
                    labels_str = ''.join(
                        f'<span style="background-color: #{label["color"]}; color: #fff; padding: 1px 4px; border-radius: 3px; margin-left: 4px;">{html.escape(label["name"])}</span>'
                        for label in labels
                    ) or 'No labels'

                    link = match.group(0)
                    if link_suffix_transform_fn:
                        link = link_suffix_transform_fn(link)

                    issue_info = f'<span title="{status_title}">{status_icon}</span> [{owner}/{repo}#{number}]({link}) {labels_str}'
                    markdown = markdown.replace(match.group(0), issue_info)
                    logger.debug(f"Processed {fetch_status_fn.__name__.split('_')[1]}: {owner}/{repo}#{number} with status: {status}")

            # Process issues
            process_matches(issue_pattern, fetch_issue_status, {'open': '🟢', 'closed': '🔴'})
            # Process PRs
            process_matches(pr_pattern, fetch_pr_status, {'open': '🟢', 'merged': '🟣', 'closed': '🔴'},
                            link_suffix_transform_fn=(lambda link: link.replace('/-/merge_requests/', '/merge_requests/')) if service == 'gitlab' else None)

        return markdown

# Setup function for entry point
def get_status():
    return Issues

