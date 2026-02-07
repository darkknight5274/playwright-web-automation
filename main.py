import uvicorn
from utils.api import app

def main():
    print("Starting Domain Activity API server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
