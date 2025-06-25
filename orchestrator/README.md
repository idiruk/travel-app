# Orchestrator Service

This service orchestrates calls to various microservices to generate travel plans.

## Configuration

The orchestrator service uses the following environment variables to configure the URLs of the microservices it calls:

-   **`LLM_API_URL`**: The URL for the LLM API.
    -   Default: `http://localhost:8000/generate`
-   **`PARSER_API_URL`**: The URL for the Parser API.
    -   Default: `http://localhost:8001/parse`
-   **`GEO_API_URL`**: The URL for the Geo API.
    -   Default: `http://localhost:8002/geocode`
-   **`MAP_API_URL`**: The URL for the Map API.
    -   Default: `http://localhost:8003/render`

If these environment variables are not set, the service will use the default values.
