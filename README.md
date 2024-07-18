# mkdocs-issues-plugin

A plugin for showing the state and labels of issues (GitHub or GitLab) in mkdocs generated docs. 

The following shows a rendering of [index.md](https://github.com/mihaigalos/mkdocs-issues-plugin/tree/main/docs):

![screenshot](https://github.com/mihaigalos/mkdocs-issues-plugin/raw/main/screenshots/mkdocs-issues-plugin.png)

## Usage

Install the mkdocs-issues-plugin package:

```bash
pip install mkdocs-issues-plugin
```


Add the following lines to you `mkdocs.yaml`:
```yaml
plugins:
    - search
    - issues:
        configs:
          - service: 'github'
            base_url: 'https://github.com'
            api_url: 'https://api.github.com'
            token: '$GITHUB_TOKEN_PUBLIC'
```

Create a GitHub token and export it before running `mkdocs serve`:

```
export GITHUB_TOKEN_PUBLIC=ghp_***
mkdocs serve
```