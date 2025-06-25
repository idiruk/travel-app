# LLM API

The LLM (Large Language Model) API service is responsible for generating natural language text, specifically travel itineraries, based on user input. It uses an underlying LLM (e.g., Ollama with a model like Llama 3) to produce the text.

## Configuration

The LLM API uses the following environment variable for configuring the model it utilizes:

-   **`LLM_MODEL_NAME_ENV`**: Specifies the name of the LLM model to be used for text generation.
    -   Purpose: Allows changing the LLM model without modifying the code. This is useful for experimenting with different models or updating to newer versions.
    -   Default: `llama3`

If this environment variable is not set, the service will use the default value. The actual availability of the model depends on the setup of the underlying LLM provider (e.g., Ollama).
