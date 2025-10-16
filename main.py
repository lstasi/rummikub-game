#!/usr/bin/env python3
"""
Main entry point for running the Rummikub application locally.

This script serves both the API backend and the UI frontend. It assumes Redis is running
on the default port (6379). For Docker setup, use docker-compose.yml instead.

Usage:
    python main.py                    # Run with default settings
    python main.py --reload          # Run with hot reload (development)
    python main.py --port 8080       # Run on custom port
    python main.py --help            # Show help
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to Python path for local development
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from rummikub.api.main import app as api_app
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install dependencies with: pip install -e .[dev]")
    sys.exit(1)


def check_redis_connection():
    """Check if Redis is accessible."""
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        print(f"✓ Redis connection successful: {redis_url}")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("Make sure Redis is running:")
        print("  - With Docker: docker run -d -p 6379:6379 redis:7-alpine")
        print("  - Or use docker-compose: docker compose up redis -d")
        print("  - Or install locally: see https://redis.io/docs/install/")
        return False


def create_app():
    """Create the combined FastAPI application with API and UI."""
    
    # Create main app
    app = FastAPI(
        title="Rummikub Game",
        description="Multiplayer Rummikub game with web interface",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Mount API routes under /api/v1 (removing /api prefix from routes)
    app.mount("/api/v1", api_app)
    
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Root endpoint that serves appropriate page based on query parameters."""
        params = dict(request.query_params)
        page = params.get('page', 'home')
        
        # Map page names to HTML files
        page_files = {
            'home': 'home.html',
            'game': 'game.html',
            'win': 'win.html'
        }
        
        # Default to home if invalid page
        html_file = page_files.get(page, 'home.html')
        
        # Serve the appropriate HTML file
        pages_path = Path(__file__).parent / "static" / "pages" / html_file
        if pages_path.exists():
            return FileResponse(str(pages_path), media_type="text/html")
        else:
            # Fallback to a simple HTML response if file doesn't exist
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Rummikub Online</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body>
                    <h1>Rummikub Online</h1>
                    <p>Page not found: {page}</p>
                    <a href="/">Go Home</a>
                </body>
                </html>
                """,
                status_code=404
            )
    
    return app


def main():
    parser = argparse.ArgumentParser(
        description="Run Rummikub application with API and UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run server on localhost:8000
  python main.py --reload          # Run with hot reload for development  
  python main.py --port 8080       # Run on port 8080
  python main.py --host 0.0.0.0    # Allow external connections
        """
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8090,
        help="Port to bind to (default: 8090)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable hot reload for development"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level (default: info)"
    )
    parser.add_argument(
        "--skip-redis-check",
        action="store_true",
        help="Skip Redis connection check on startup"
    )
    
    args = parser.parse_args()
    
    # Check Redis connection unless skipped
    if not args.skip_redis_check:
        if not check_redis_connection():
            print("\nUse --skip-redis-check to start anyway (API will fail on Redis operations)")
            return 1
    
    print("\n🚀 Starting Rummikub application...")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Game UI: http://{args.host}:{args.port}")
    print(f"   API Docs: http://{args.host}:{args.port}/docs")
    print(f"   Reload: {'enabled' if args.reload else 'disabled'}")
    print(f"   Log level: {args.log_level}")
    
    if args.reload:
        print("\n💡 Hot reload is enabled - changes will restart the server")
    
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run the server with appropriate configuration for reload
    if args.reload:
        # For reload to work, we need to pass the app as an import string
        uvicorn.run(
            "main:create_app",
            factory=True,
            host=args.host,
            port=args.port,
            reload=True,
            log_level=args.log_level,
            access_log=True,
            reload_dirs=["src", "static"],
        )
    else:
        # Create the combined app
        app = create_app()
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=False,
            log_level=args.log_level,
            access_log=True,
        )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())