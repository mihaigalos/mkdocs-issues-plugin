# mkdocs-breadcrumbs

Experimental mkdocs location-based breadcrumbs navigation.

These directly get prepended to rendered Markdown.

## Setup

Install the plugin using pip:

```bash
pip install mkdocs-breadcrumbs
```

Activate the plugin in `mkdocs.yml`:
```yaml
plugins:
  - search
  - breadcrumbs
```

## Config

* `start_depth` - An int representing at which depth the plugin is running the logic. The depth represents the number of slashes in a URL path (i.e.: /home/ has depth 2). 

