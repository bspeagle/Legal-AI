#!/usr/bin/env python3
"""
Launcher script for Legal AI Virtual Courtroom
Runs both the FastAPI backend and Streamlit frontend in parallel using subprocesses
"""
import os
import subprocess
import sys
import time
import webbrowser
import signal
import atexit

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 8501
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"

# Set environment variable for API URL to be used by the frontend
os.environ["API_URL"] = f"{BACKEND_URL}/api"

# Store process IDs for cleanup
processes = []

def cleanup():
    """Clean up subprocesses on exit"""
    print("\nShutting down services...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"Error terminating process: {e}")
    print("All services stopped.")

# Register cleanup function
atexit.register(cleanup)

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    print("\nInterrupt signal received.")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def ensure_directory_exists(path):
    """Ensure the directory structure exists"""
    if not os.path.exists(path):
        os.makedirs(path)

def run_backend():
    """Start the FastAPI backend server"""
    print(f"Starting backend server at {BACKEND_URL}...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.main:app", 
        "--host", "0.0.0.0", 
        "--port", str(BACKEND_PORT),
        "--reload"
    ]
    
    backend_process = subprocess.Popen(
        backend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(backend_process)
    return backend_process

def run_frontend():
    """Start the Streamlit frontend"""
    print(f"Starting frontend at {FRONTEND_URL}...")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port", str(FRONTEND_PORT)
    ]
    
    frontend_process = subprocess.Popen(
        frontend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(frontend_process)
    return frontend_process

def monitor_processes(backend_process, frontend_process):
    """Monitor the running processes and display their output"""
    import threading
    import queue
    
    output_queue = queue.Queue()
    
    def enqueue_output(proc, name):
        for line in iter(proc.stdout.readline, ''):
            output_queue.put((name, line.strip()))
        proc.stdout.close()
    
    # Start threads to read output
    backend_thread = threading.Thread(target=enqueue_output, args=(backend_process, 'BACKEND'))
    backend_thread.daemon = True
    backend_thread.start()
    
    frontend_thread = threading.Thread(target=enqueue_output, args=(frontend_process, 'FRONTEND'))
    frontend_thread.daemon = True
    frontend_thread.start()
    
    # Check for process exit and print output
    while True:
        # Check if any process has exited
        if backend_process.poll() is not None:
            print(f"Backend process exited with code {backend_process.returncode}")
            sys.exit(1)
        if frontend_process.poll() is not None:
            print(f"Frontend process exited with code {frontend_process.returncode}")
            sys.exit(1)
        
        # Display output
        try:
            name, line = output_queue.get(timeout=0.1)
            print(f"[{name}] {line}")
        except queue.Empty:
            pass
        except KeyboardInterrupt:
            print("\nInterrupt received, shutting down...")
            break

def wait_for_service(url, max_retries=10, delay=2):
    """Wait for a service to become available"""
    import urllib.request
    import urllib.error
    
    print(f"Waiting for {url} to become available...")
    for i in range(max_retries):
        try:
            urllib.request.urlopen(url)
            print(f"Service at {url} is now available")
            return True
        except urllib.error.URLError:
            print(f"Waiting for service to start ({i+1}/{max_retries})...")
            time.sleep(delay)
    
    print(f"Service at {url} failed to start after {max_retries} attempts")
    return False

def main():
    """Main function to run the application"""
    print("Starting Legal AI Virtual Courtroom...")
    
    # Ensure necessary directories exist
    ensure_directory_exists("data")
    ensure_directory_exists("data/uploads")
    ensure_directory_exists("data/db")
    
    # Start services
    backend_process = run_backend()
    time.sleep(3)  # Give backend a moment to start
    frontend_process = run_frontend()
    
    # Wait for services to be available
    if wait_for_service(f"{BACKEND_URL}/docs"):
        # Open browser windows
        print("Opening application in browser...")
        webbrowser.open(FRONTEND_URL)
        time.sleep(1)
        webbrowser.open(f"{BACKEND_URL}/docs")  # Open API docs
    
    # Monitor the processes
    try:
        monitor_processes(backend_process, frontend_process)
    except KeyboardInterrupt:
        print("\nInterrupt received, shutting down...")

if __name__ == "__main__":
    main()
