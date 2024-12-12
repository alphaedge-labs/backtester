import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from utils.logging import logger
from utils.datetime import get_ist_time
from routes.auth import router as auth_router
from database.mongodb import init_db
from settings.env import PORT

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting services...")
    yield
    logger.info("Shutting down services...")

app = FastAPI(lifespan=lifespan, debug=True)

@app.get("/health")
def health_check():
    return {"status": "running", "message": "AlphaEdge Backtester is running", "datetime": get_ist_time()}

async def main():
    services = {}

    try:
        # Initialize database connection
        await init_db()

        global loop
        loop = asyncio.get_event_loop()

        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=PORT,
            loop="asyncio"
        )
        server = uvicorn.Server(config)
        fastapi_task = loop.create_task(server.serve())
        
        # Wait indefinitely until interrupted
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, initiating shutdown...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        logger.info("Shutting down services...")
        
        # Cleanup FastAPI
        if 'fastapi_task' in locals():
            fastapi_task.cancel()
            try:
                await fastapi_task
            except asyncio.CancelledError:
                pass

        logger.info("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt in main thread")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise