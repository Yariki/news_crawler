
RESOURCE_ACTIONS = {
    "permissions": [
        {
            "resource": "source",
            "actions": ["create", "read", "update", "delete", "run"]
        },
        {
            "resource": "article",
            "actions": ["read"]
        },
        {
            "resource": "keyword",
            "actions": ["create", "read", "update", "delete"]
        },
        {
            "resource":"alert",
            "actions":["read"]
        },
        {
            "resource":"job",
            "actions":["read"]
        },
        {
            "resource":"dashboard",
            "actions":["read"]
        }
    ]
}