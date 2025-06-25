# Geo API

The Geo API service is responsible for geocoding location names (cities, landmarks, hotels, etc.) into geographical coordinates (latitude and longitude). It uses the Nominatim service from OpenStreetMap for geocoding.

## Configuration

The Geo API uses the following environment variables for configuring its connection to the Nominatim service:

-   **`NOMINATIM_URL_ENV`**: The URL of the Nominatim service to be used for geocoding.
    -   Purpose: Allows specifying a different Nominatim instance (e.g., a self-hosted one).
    -   Default: `https://nominatim.openstreetmap.org/search`
-   **`NOMINATIM_USER_AGENT_ENV`**: The User-Agent string to be sent with requests to the Nominatim service.
    -   Purpose: Required by Nominatim's usage policy to identify the application. It's important to set a custom User-Agent that is descriptive and allows them to contact you if needed.
    -   Default: `travel-app/1.0`

If these environment variables are not set, the service will use the default values. It is highly recommended to set a custom `NOMINATIM_USER_AGENT_ENV` that includes contact information (like an email address or project website) as per Nominatim's usage policy.
