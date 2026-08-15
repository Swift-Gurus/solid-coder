"""Emit deterministic mixed-category units for live flow-engine validation."""

import json


print(
    json.dumps(
        {
            "units": [
                {
                    "text": "Is the service healthy?",
                    "category": "question",
                },
                {
                    "text": "The service is healthy.",
                    "category": "statement",
                },
            ]
        }
    )
)
