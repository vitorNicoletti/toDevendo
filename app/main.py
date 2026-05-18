import uvicorn
from src.create_wpp_connection import ensure_connected

if __name__ == "__main__":
    ensure_connected()
    uvicorn.run("src.app:app", host="0.0.0.0", port=3001, reload=False)
