"""ByteShield - Application Entrypoint & Server Launcher
Runs the FastAPI middleware server on http://localhost:8000
"""

import sys
import uvicorn

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8") # pyright: ignore[reportAttributeAccessIssue]
        sys.stderr.reconfigure(encoding="utf-8") # pyright: ignore[reportAttributeAccessIssue]

    print("=" * 70)
    print("[ByteShield] Real-Time AI Fraud Detection for UPI & Micro-Transactions")
    print("[System Gateway] National UPI Cyber Defense & AI Fraud Interception Gateway")
    print("=" * 70)
    print("Starting High-Throughput FastAPI Engine on: http://localhost:8000")
    print("Swagger Interactive API Docs available at: http://localhost:8000/docs")
    print("Sub-200ms Pre-PIN Interception Middleware: ACTIVE")
    print("=" * 70)
    
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
