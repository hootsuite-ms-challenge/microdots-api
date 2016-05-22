Microdots API Server
====================

This repository contains the source code for the Microdots API Server. It stores information about endpoints and their usage from other API microservices. This data can be used to plot a graph representing their dependencies.

# Installation

[Django][django] and its dependencies are specified in `requirements.txt`. They can be installed (preferably in a [virtualenv][venv]) with:

    $ pip install -r requirements.txt

The codebase is compatible with **Python 3.4+**.

# External dependencies

Neo4j and Redis are used to store the graph data. If they aren't available in the same machine which the API server being executed, and assuming [Docker][docker] is installed, both of them can be started with:

    $ make services

If those services are running from non-standard locations, the environment variables `GRAPHENEDB_URL` and `REDIS_URL` can be used to define the address of Neo4j and Redis, respectively. If Docker is being used, there's no need to worry about them.

# Running

The development server can be started with:

    $ make run

# API resources

**Endpoint**: `/microdot/` 

**Method**: `POST`

| Field | Type | Description |
| ----- | ---- | ----------- |
| `origin` | `string` | Microservice which originated the request. |
| `target` | `string` | Microservice which is the target of the originated request. |
| `endpoint` | `string` | Endpoint requested by `origin`. |
| `method` | `string` | HTTP method used in the request. |

**Endpoint**: `/graph/` 

**Method**: `GET`

This endpoint returns a JSON representing the dependency graph between microservices.

    {
        "nodes": [
            {
                "label": "portal",
                "endpoints": [],
                "value": 5.0,
                "id": "portal"
            },
            {
                "label": "payments",
                "endpoints": [
                    "GET /list/"
                ],
                "value": 2.0,
                "id": "payments"
            }
        ],
        "edges": [
            {
                "endpoints": [
                    {
                        "endpoint": "GET /list/",
                        "access": 1
                    }
                ],
                "to": "payments",
                "id": "portal_payments",
                "usage": "100.0%",
                "from": "portal"
            }
        ]
    }

# Tests

There are integration tests, which can be executed with:

    $ make test

**Warning**: *the test suit purges both Neo4j and Redis data every time they are run. All of it. Not just what is being used by the application. Please don't do this on a machine which stores data that cannot be discarded.*

# Cleaning up

To remove the Docker containers (also losing their data), run:

    $ make clean


[django]: https://www.djangoproject.com/
[docker]: https://www.docker.com/
[venv]: https://virtualenv.pypa.io/en/stable/
