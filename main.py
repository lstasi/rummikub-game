#!/usr/bin/env python3
"""
Main entry point for running the Rummikub API server locally.

This script is intended for local development. It assumes Redis is running
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


def main():
    parser = argparse.ArgumentParser(
        description="Run Rummikub API server locally",
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
        default=8000,
        help="Port to bind to (default: 8000)"
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
    
    print("\n🚀 Starting Rummikub API server...")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Docs: http://{args.host}:{args.port}/docs")
    print(f"   Reload: {'enabled' if args.reload else 'disabled'}")
    print(f"   Log level: {args.log_level}")
    
    if args.reload:
        print("\n💡 Hot reload is enabled - changes to Python files will restart the server")
    
    print("\nPress Ctrl+C to stop the server\n")
    
    # Run the server
    uvicorn.run(
        "rummikub.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True,
        reload_dirs=["src"] if args.reload else None,
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())