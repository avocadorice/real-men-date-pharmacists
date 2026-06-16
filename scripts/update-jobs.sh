#!/bin/bash
# Exit on error
set -e

# Change directory to the repository root
cd "$(dirname "$0")/.."

echo "🚀 Starting job scrape..."
python3 src/fetcher.py

echo "📦 Exporting database to src/web/jobs.json..."
python3 -c "import sqlite3, json; conn = sqlite3.connect('jobs.db'); conn.row_factory = sqlite3.Row; cursor = conn.cursor(); cursor.execute('SELECT * FROM jobs'); jobs = [dict(row) for row in cursor.fetchall()]; open('src/web/jobs.json', 'w').write(json.dumps(jobs, indent=2))"

echo "💾 Committing and pushing updated jobs..."
git add src/web/jobs.json
# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "✨ No new jobs found. Repository is up to date."
else
    git commit -m "Auto-update scraped jobs data"
    git push origin main
    echo "🎉 Successfully pushed update to GitHub. Pages deployment will complete shortly!"
fi
