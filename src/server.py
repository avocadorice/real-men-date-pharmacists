import http.server
import socketserver
import json
import os
import urllib.parse
from database import get_db_connection
from fetcher import fetch_jobs_from_serpapi, save_jobs_to_db

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")

class JobMonitorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        # Allow CORS for development ease
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        
        # API: Get all jobs
        if path == "/api/jobs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, company, location, via, description, salary, 
                       apply_link, posted_at, distance_miles, status, notes, 
                       fetched_date, applied_date
                FROM jobs 
                ORDER BY 
                    CASE WHEN distance_miles IS NULL THEN 9999 ELSE distance_miles END ASC,
                    fetched_date DESC
            """)
            jobs = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            self.wfile.write(json.dumps(jobs).encode('utf-8'))
            return
            
        # Default: serve static files
        super().do_GET()

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        path = url_parsed.path
        
        # Parse content length
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # API: Update job status
        if path.startswith("/api/jobs/") and path.endswith("/status"):
            parts = path.split('/')
            job_id = parts[3] # /api/jobs/<job_id>/status
            new_status = data.get("status")
            
            if new_status not in ['new', 'seen', 'applied', 'archived', 'rejected']:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid status value")
                return
                
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if new_status == 'applied':
                import datetime
                applied_date = datetime.date.today().isoformat()
                cursor.execute("""
                    UPDATE jobs 
                    SET status = ?, applied_date = ?
                    WHERE id = ?
                """, (new_status, applied_date, job_id))
            else:
                cursor.execute("""
                    UPDATE jobs 
                    SET status = ?, applied_date = NULL
                    WHERE id = ?
                """, (new_status, job_id))
                
            conn.commit()
            conn.close()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "job_id": job_id, "status": new_status}).encode('utf-8'))
            return

        # API: Update job notes
        elif path.startswith("/api/jobs/") and path.endswith("/notes"):
            parts = path.split('/')
            job_id = parts[3] # /api/jobs/<job_id>/notes
            notes = data.get("notes", "")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET notes = ?
                WHERE id = ?
            """, (notes, job_id))
            conn.commit()
            conn.close()
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "job_id": job_id, "notes": notes}).encode('utf-8'))
            return

        # API: Trigger Scrape/Fetch
        elif path == "/api/scrape":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            # Run fetcher (will automatically check env variable, fallback to mock if empty)
            raw_jobs = fetch_jobs_from_serpapi()
            new_added = save_jobs_to_db(raw_jobs)
            
            self.wfile.write(json.dumps({
                "success": True, 
                "total_fetched": len(raw_jobs), 
                "new_added": new_added
            }).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    # Make sure web directory exists
    os.makedirs(WEB_DIR, exist_ok=True)
    
    # Simple check for index.html - if it doesn't exist, we will create it next.
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), JobMonitorHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run_server()
