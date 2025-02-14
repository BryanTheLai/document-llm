# Gemini Chatbot Application

This project is a simple chatbot powered by Google's Gemini model. It uses Streamlit for the user interface and LiteLLM to interact with the Gemini API.

## Prerequisites

-   [Docker](https://www.docker.com/)
-   [Docker Compose](https://www.docker.com/)

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Create a `.env` file:**

    Create a `.env` file in the root directory and add your Google API key:

    ```
    GOOGLE_API_KEY=YOUR_API_KEY
    ```

3.  **Run the application with Docker Compose:**

    ```bash
    docker-compose up -d --force-recreate
    ```

    This command does the following:

    -   `docker-compose up`: Starts the services defined in `docker-compose.yml`.
    -   `-d`: Runs the containers in detached mode (in the background).
    -   `--force-recreate`: Recreates containers even if their configuration hasn't changed.

4.  **Access the application:**

    Open your web browser and go to `http://127.0.0.1:8501`.

## File Structure

```
document-llm/             # Root project directory
├── src/                        # Source code directory
│   └── app/                    # Application package
│       ├── __init__.py         # Makes 'app' a Python package
│       ├── models.py           # Data models
│       ├── prompts.py          # Gemini prompts
│       ├── services.py         # Business logic
│       ├── utils.py            # Utility functions
│       ├── views.py            # UI views (if separate)
│       ├── routers.py          # API routes (FastAPI)
├── main.py                     # Main application file
├── docker-compose.yml          # Docker setup
├── dockerfile                  # Docker image definition
└── README.md                   # Project documentation
```

## Stopping the Application

To stop and remove the containers, run:

```bash
docker-compose down
```

## Cleaning Up

To remove the Docker image, run:

```bash
docker rmi document-llm --force
```

**Note:** The `--force` flag is needed if the image is currently in use by a container.  You might see an error if the image doesn't exist, which is fine.

## Running the Application Locally (Without Docker)

1.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    ```

2.  **Activate the virtual environment:**

    ```bash
    venv/Scripts/Activate  # On Windows
    source venv/bin/activate # On macOS and Linux
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit application:**

    ```bash
    streamlit run src/main.py --server.address=0.0.0.0
    ```

    **Note:**  Make sure you are running the command from the root directory of your project.

## Troubleshooting

-   If you encounter errors related to the API key, double-check that the `.env` file is correctly configured and that the API key is valid.
-   If you encounter errors related to the Docker image, ensure that Docker is properly installed and running.
-   If you have any other issues, consult the documentation for Docker, Docker Compose, Streamlit, and LiteLLM.
