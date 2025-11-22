import uvicorn

from src.api.app import app
from src.classifier.configuration import SERVE_CONFIG


def main():
    serve_params = SERVE_CONFIG["serve_params"]
    uvicorn.run(
        app,
        host=serve_params["host"],
        port=int(serve_params["port"]),
        log_level="info"
    )

if __name__ == "__main__":
    main()
