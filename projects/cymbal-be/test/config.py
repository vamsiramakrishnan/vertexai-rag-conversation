import os

ENV_SETTINGS = {
    'dev': {
        'url': "...",
        'headers': {'x-api-key': os.getenv('DEV_API_KEY', 'DEFAULT_DEV_API_KEY'), 'Content-Type': 'application/json'},
    },
    'uat': {
        'url': "...",
        'headers': {'x-api-key': os.getenv('UAT_API_KEY', 'DEFAULT_UAT_API_KEY'), 'Content-Type': 'application/json'},
    },
    'local': {
        'url': "http://localhost:8080/routeragent",
        'headers': {'Authorization': 'Bearer {}'.format(os.getenv('LOCAL_BEARER_TOKEN', 'DEFAULT_LOCAL_BEARER_TOKEN')), 'Content-Type': 'application/json'},
    }
}