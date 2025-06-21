from uvicorn import run
from server import create_app
from server.config import settings as s

development = s.FASTAPI_ENV == "development"

app = create_app()

if __name__ == "__main__":
    run("server.__main__:app", host="0.0.0.0", port=s.PORT, reload=development)
