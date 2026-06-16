import os
import json
import urllib.request
import urllib.parse
import hashlib
import sqlite3
from database import get_db_connection

# Local distance mapping (in miles) from San Jose (95120)
# Covers South Bay, East Bay, Peninsula, and common float destinations.
DISTANCE_MAP = {
    "san jose": 5.0,
    "almaden": 3.0,
    "los gatos": 8.0,
    "campbell": 9.0,
    "santa clara": 11.0,
    "saratoga": 11.0,
    "cupertino": 13.0,
    "sunnyvale": 16.0,
    "mountain view": 19.0,
    "milpitas": 16.0,
    "palo alto": 24.0,
    "los altos": 20.0,
    "menlo park": 26.0,
    "redwood city": 30.0,
    "san mateo": 38.0,
    "fremont": 27.0,
    "newark": 26.0,
    "union city": 31.0,
    "hayward": 36.0,
    "morgan hill": 18.0,
    "gilroy": 28.0,
    "salinas": 58.0,
    "los banos": 78.0,
    "watsonville": 40.0,
    "santa cruz": 33.0,
    "monterey": 68.0,
    "south san francisco": 46.0,
    "san francisco": 52.0,
    "oakland": 46.0,
    "berkeley": 50.0,
    "pleasanton": 43.0,
    "livermore": 48.0,
    "remote": 0.0,
    "anywhere": 0.0,
    "work from home": 0.0
}

def get_distance_from_location(location_str):
    if not location_str:
        return None
    
    loc_lower = location_str.lower()
    
    # Check for remote indicators
    if "remote" in loc_lower or "work from home" in loc_lower or "wfh" in loc_lower:
        return 0.0
        
    # Match against our distance map
    for city, dist in DISTANCE_MAP.items():
        if city in loc_lower:
            return dist
            
    # Default fallback
    return None

def fetch_jobs_from_serpapi(api_key=None, query="pharmacist", location="95120"):
    if not api_key:
        api_key = os.environ.get("SERPAPI_API_KEY")
        
    if not api_key:
        print("SERPAPI_API_KEY not found. Using mock jobs for testing.")
        return get_mock_jobs()
        
    params = {
        "engine": "google_jobs",
        "q": query,
        "l": location,
        "api_key": api_key
    }
    
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    print(f"Fetching job data from SerpAPI for query '{query}' near {location}...")
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        jobs = data.get("jobs_results", [])
        print(f"Successfully retrieved {len(jobs)} jobs from SerpAPI.")
        return format_serpapi_jobs(jobs)
    except Exception as e:
        print(f"Error fetching from SerpAPI: {e}")
        print("Falling back to mock jobs.")
        return get_mock_jobs()

def format_serpapi_jobs(jobs):
    formatted = []
    for job in jobs:
        title = job.get("title", "")
        company = job.get("company_name", "")
        location = job.get("location", "")
        via = job.get("via", "")
        description = job.get("description", "")
        
        # Parse job ID
        job_id = job.get("job_id")
        if not job_id:
            # Generate stable hash if no job_id is returned
            hash_input = f"{title}-{company}-{location}"
            job_id = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
            
        # Extract salary
        salary = ""
        extensions = job.get("detected_extensions", {})
        if "salary" in extensions:
            salary = extensions["salary"]
        else:
            # Check description or other extensions
            for ext in job.get("extensions", []):
                if "$" in ext or "hour" in ext or "year" in ext:
                    salary = ext
                    break
                    
        # Apply link
        apply_link = ""
        apply_options = job.get("apply_options", [])
        if apply_options:
            apply_link = apply_options[0].get("link", "")
            
        posted_at = ""
        if "posted_at" in extensions:
            posted_at = extensions["posted_at"]
        elif job.get("extensions"):
            posted_at = job["extensions"][0] # Often first extension is "X hours ago"
            
        formatted.append({
            "id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "via": via,
            "description": description,
            "salary": salary,
            "apply_link": apply_link,
            "posted_at": posted_at
        })
    return formatted

def get_mock_jobs():
    return [
        {
            "id": "mock_costco_1",
            "title": "Staff Pharmacist (Part-Time / Per Diem)",
            "company": "Costco Wholesale",
            "location": "San Jose, CA (Almaden Warehouse)",
            "via": "via Costco Careers",
            "description": "Costco Wholesale is looking for a licensed Staff Pharmacist for our Almaden location. Responsible for prescription dispensing, patient counseling, immunization delivery, and providing exceptional member service. Closed on Sundays. No drive-thru. Highly competitive pay.",
            "salary": "$78.50 - $84.00 an hour",
            "apply_link": "https://www.costco.com/jobs.html",
            "posted_at": "2 hours ago"
        },
        {
            "id": "mock_kaiser_1",
            "title": "Outpatient Clinical Pharmacist (Ambulatory Care)",
            "company": "Kaiser Permanente",
            "location": "Santa Clara, CA",
            "via": "via Kaiser Careers",
            "description": "Join our outpatient care team. Under collaborative practice protocols (CDTM), manage chronic conditions including anticoagulation, hypertension, and diabetes. Conduct Medication Therapy Management (MTM) reviews using Epic EMR. Requires CA RPh license and 1,200 hours clinical experience or PGY1.",
            "salary": "$104.50 - $107.00 an hour",
            "apply_link": "https://jobs.kp.org",
            "posted_at": "1 day ago"
        },
        {
            "id": "mock_optum_1",
            "title": "Clinical Pharmacist - Prior Authorization (Remote)",
            "company": "OptumRx",
            "location": "Remote, CA",
            "via": "via LinkedIn",
            "description": "Perform clinical reviews of prior authorization requests, step-therapy overrides, and formulary exceptions. Ensure CMS compliance and quality guidelines are met. Review complex clinical drug histories telephonically with providers. 100% remote. Retail pharmacists welcome.",
            "salary": "$62.00 - $68.00 an hour",
            "apply_link": "https://www.optum.com/careers",
            "posted_at": "5 hours ago"
        },
        {
            "id": "mock_safeway_1",
            "title": "Staff Pharmacist (Full-Time)",
            "company": "Safeway",
            "location": "Campbell, CA",
            "via": "via Indeed",
            "description": "Manage grocery pharmacy operations. Perform prescription verification, counsel members, and coordinate vaccine programs. Fast-paced, community-focused environment. Competitive benefits and retirement matching.",
            "salary": "$72.00 - $78.00 an hour",
            "apply_link": "https://www.safeway.com/careers",
            "posted_at": "3 days ago"
        },
        {
            "id": "mock_walmart_salinas",
            "title": "Floater Pharmacist (Part-Time)",
            "company": "Walmart Pharmacy",
            "location": "Salinas, CA",
            "via": "via Walmart Careers",
            "description": "Provide coverage at various Walmart pharmacy locations in the district. Dispense prescriptions, administer immunizations, manage tech workflows, and ensure regulatory compliance. Requires travel across the district (mileage reimbursed).",
            "salary": "$75.00 - $80.00 an hour",
            "apply_link": "https://careers.walmart.com",
            "posted_at": "Just posted"
        }
    ]

def save_jobs_to_db(jobs):
    conn = get_db_connection()
    cursor = conn.cursor()
    new_jobs_count = 0
    
    for job in jobs:
        # Calculate distance
        distance = get_distance_from_location(job["location"])
        
        try:
            cursor.execute("""
                INSERT INTO jobs (id, title, company, location, via, description, salary, apply_link, posted_at, distance_miles, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
            """, (
                job["id"],
                job["title"],
                job["company"],
                job["location"],
                job["via"],
                job["description"],
                job["salary"],
                job["apply_link"],
                job["posted_at"],
                distance
            ))
            new_jobs_count += 1
        except sqlite3.IntegrityError:
            # Job already exists, update dynamic fields but keep status, notes, applied_date
            cursor.execute("""
                UPDATE jobs
                SET salary = ?, posted_at = ?, apply_link = ?
                WHERE id = ?
            """, (job["salary"], job["posted_at"], job["apply_link"], job["id"]))
            
    conn.commit()
    conn.close()
    return new_jobs_count

if __name__ == "__main__":
    # Test fetcher
    jobs = fetch_jobs_from_serpapi()
    new_count = save_jobs_to_db(jobs)
    print(f"Scrape completed: {len(jobs)} processed, {new_count} new jobs added to database.")
