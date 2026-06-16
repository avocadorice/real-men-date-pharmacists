// Global state
let allJobs = [];
let isStaticMode = false;

// DOM Elements
const jobsListEl = document.getElementById("jobs-list");
const statTotalEl = document.getElementById("stat-total");
const statCommuteEl = document.getElementById("stat-avg-commute");
const statAppliedEl = document.getElementById("stat-applied");
const statNewEl = document.getElementById("stat-new");
const feedCountEl = document.getElementById("feed-count");

// Inputs
const searchInput = document.getElementById("search-input");
const statusFilter = document.getElementById("filter-status");
const distanceFilter = document.getElementById("filter-distance");
const employerFilter = document.getElementById("filter-employer");
const scrapeBtn = document.getElementById("scrape-btn");

// Modal Elements
const notesModal = document.getElementById("notes-modal");
const modalJobTitle = document.getElementById("modal-job-title");
const modalJobId = document.getElementById("modal-job-id");
const modalNotesText = document.getElementById("modal-notes-text");

// Initialize page
document.addEventListener("DOMContentLoaded", () => {
    setupTabSwitching();
    loadJobs();
    
    // Setup event listeners for filtering
    searchInput.addEventListener("input", filterAndRenderJobs);
    statusFilter.addEventListener("change", filterAndRenderJobs);
    distanceFilter.addEventListener("change", filterAndRenderJobs);
    employerFilter.addEventListener("change", filterAndRenderJobs);
    
    // Scrape button click handler
    scrapeBtn.addEventListener("click", triggerScrape);
});

// ==========================================================================
// Tab Navigation
// ==========================================================================
function setupTabSwitching() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            
            navButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(`tab-${tabId}`).classList.add("active");
        });
    });
}

// ==========================================================================
// API & Local Fallback Handlers
// ==========================================================================
function updateStatusIndicator(isConnected) {
    const dot = document.querySelector(".status-dot");
    const label = document.querySelector(".status-label");
    if (dot && label) {
        if (isConnected) {
            dot.className = "status-dot green";
            label.textContent = "Database Connected";
        } else {
            dot.className = "status-dot orange";
            label.textContent = "Static Mode (GitHub Pages)";
        }
    }
}

async function loadJobs() {
    showLoading();
    try {
        const response = await fetch("/api/jobs");
        if (!response.ok) throw new Error("API not available");
        allJobs = await response.json();
        isStaticMode = false;
        updateStatusIndicator(true);
    } catch (error) {
        console.log("Failed to connect to local database server, falling back to static jobs.json:", error);
        isStaticMode = true;
        updateStatusIndicator(false);
        try {
            const response = await fetch("jobs.json");
            allJobs = await response.json();
            
            // Merge localStorage changes in static mode
            allJobs.forEach(job => {
                const storedStatus = localStorage.getItem(`job_status_${job.id}`);
                const storedNotes = localStorage.getItem(`job_notes_${job.id}`);
                const storedAppliedDate = localStorage.getItem(`job_applied_date_${job.id}`);
                
                if (storedStatus) job.status = storedStatus;
                if (storedNotes) job.notes = storedNotes;
                if (storedAppliedDate) job.applied_date = storedAppliedDate;
            });
        } catch (jsonError) {
            console.error("Error loading static jobs.json:", jsonError);
            jobsListEl.innerHTML = `
                <div class="empty-state">
                    <p>⚠️ Failed to fetch job data from the local database or static jobs.json.</p>
                </div>
            `;
            return;
        }
    }
    updateStats();
    filterAndRenderJobs();
}

async function triggerScrape() {
    if (isStaticMode) {
        alert("⚠️ Scan New Postings is only available when running locally with the python backend. GitHub Pages hosts static files only.");
        return;
    }
    
    scrapeBtn.disabled = true;
    scrapeBtn.innerHTML = '<span class="spinner" style="width:16px;height:16px;display:inline-block;margin:0 8px 0 0;"></span> Scanning...';
    
    try {
        const response = await fetch("/api/scrape", { method: "POST" });
        const result = await response.json();
        
        if (result.success) {
            alert(`Scan finished!\nTotal jobs checked: ${result.total_fetched}\nNew jobs added: ${result.new_added}`);
            loadJobs();
        } else {
            alert("Scrape failed. Check terminal logs.");
        }
    } catch (error) {
        console.error("Error during scan:", error);
        alert("Network error occurred during scan.");
    } finally {
        scrapeBtn.disabled = false;
        scrapeBtn.innerHTML = '<span class="btn-icon">🔄</span> Scan New Postings';
    }
}

async function updateJobStatus(jobId, status) {
    if (isStaticMode) {
        const jobIndex = allJobs.findIndex(j => j.id === jobId);
        if (jobIndex !== -1) {
            allJobs[jobIndex].status = status;
            localStorage.setItem(`job_status_${jobId}`, status);
            if (status === 'applied') {
                const today = new Date().toISOString().split('T')[0];
                allJobs[jobIndex].applied_date = today;
                localStorage.setItem(`job_applied_date_${jobId}`, today);
            } else {
                allJobs[jobIndex].applied_date = null;
                localStorage.removeItem(`job_applied_date_${jobId}`);
            }
            updateStats();
            filterAndRenderJobs();
        }
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status })
        });
        
        const result = await response.json();
        if (result.success) {
            // Update local state
            const jobIndex = allJobs.findIndex(j => j.id === jobId);
            if (jobIndex !== -1) {
                allJobs[jobIndex].status = status;
                if (status === 'applied') {
                    allJobs[jobIndex].applied_date = new Date().toISOString().split('T')[0];
                } else {
                    allJobs[jobIndex].applied_date = null;
                }
            }
            updateStats();
            filterAndRenderJobs();
        }
    } catch (error) {
        console.error("Failed to update status:", error);
        alert("Failed to update status.");
    }
}

async function saveJobNotes() {
    const jobId = modalJobId.value;
    const notes = modalNotesText.value;
    
    if (isStaticMode) {
        const job = allJobs.find(j => j.id === jobId);
        if (job) {
            job.notes = notes;
            localStorage.setItem(`job_notes_${jobId}`, notes);
        }
        closeNotesModal();
        filterAndRenderJobs();
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/notes`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ notes })
        });
        
        const result = await response.json();
        if (result.success) {
            // Update local state
            const job = allJobs.find(j => j.id === jobId);
            if (job) job.notes = notes;
            
            closeNotesModal();
            filterAndRenderJobs();
        }
    } catch (error) {
        console.error("Failed to save notes:", error);
        alert("Failed to save notes.");
    }
}

// ==========================================================================
// Filtering & Calculation
// ==========================================================================
function updateStats() {
    statTotalEl.textContent = allJobs.length;
    statNewEl.textContent = allJobs.filter(j => j.status === 'new').length;
    statAppliedEl.textContent = allJobs.filter(j => j.status === 'applied').length;
    
    // Calculate average commute distance for local/non-remote jobs
    const localJobs = allJobs.filter(j => j.distance_miles !== null && j.distance_miles > 0);
    if (localJobs.length > 0) {
        const avg = localJobs.reduce((acc, curr) => acc + curr.distance_miles, 0) / localJobs.length;
        statCommuteEl.textContent = avg.toFixed(1) + " mi";
    } else {
        statCommuteEl.textContent = "-";
    }
}

function filterAndRenderJobs() {
    const query = searchInput.value.toLowerCase().trim();
    const statusVal = statusFilter.value;
    const distanceVal = distanceFilter.value;
    const employerVal = employerFilter.value;
    
    const filtered = allJobs.filter(job => {
        // Search filter
        const matchesSearch = 
            job.title.toLowerCase().includes(query) ||
            job.company.toLowerCase().includes(query) ||
            job.description.toLowerCase().includes(query);
            
        // Status filter
        const matchesStatus = statusVal === 'all' || job.status === statusVal;
        
        // Distance filter
        let matchesDistance = true;
        if (distanceVal !== 'all') {
            if (distanceVal === 'remote') {
                matchesDistance = job.distance_miles === 0 || job.location.toLowerCase().includes("remote");
            } else {
                const limit = parseFloat(distanceVal);
                matchesDistance = job.distance_miles !== null && job.distance_miles <= limit && job.distance_miles > 0;
            }
        }
        
        // Employer filter
        let matchesEmployer = true;
        if (employerVal !== 'all') {
            const comp = job.company.toLowerCase();
            if (employerVal === 'costco') {
                matchesEmployer = comp.includes("costco");
            } else if (employerVal === 'kaiser') {
                matchesEmployer = comp.includes("kaiser");
            } else if (employerVal === 'safeway') {
                matchesEmployer = comp.includes("safeway") || comp.includes("albertsons");
            } else if (employerVal === 'other') {
                matchesEmployer = !comp.includes("costco") && !comp.includes("kaiser") && !comp.includes("safeway") && !comp.includes("albertsons");
            }
        }
        
        return matchesSearch && matchesStatus && matchesDistance && matchesEmployer;
    });
    
    feedCountEl.textContent = `Showing ${filtered.length} jobs`;
    renderJobsList(filtered);
}

// ==========================================================================
// Rendering HTML elements
// ==========================================================================
function showLoading() {
    jobsListEl.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Loading pharmacist listings...</p>
        </div>
    `;
}

function renderJobsList(jobs) {
    if (jobs.length === 0) {
        jobsListEl.innerHTML = `
            <div class="empty-state">
                <p>🔍 No matching pharmacist opportunities found. Adjust your search or filters.</p>
            </div>
        `;
        return;
    }
    
    jobsListEl.innerHTML = "";
    jobs.forEach(job => {
        // Determine theme card color
        let themeClass = "";
        const comp = job.company.toLowerCase();
        if (comp.includes("costco")) themeClass = "costco";
        else if (comp.includes("kaiser")) themeClass = "kaiser";
        else if (comp.includes("safeway") || comp.includes("albertsons")) themeClass = "safeway";
        else if (job.distance_miles === 0 || job.location.toLowerCase().includes("remote")) themeClass = "remote";
        
        // Create job card
        const card = document.createElement("div");
        card.className = `job-card ${themeClass}`;
        
        // Formulate distance badge text
        let distanceText = "";
        let distanceClass = "badge-distance";
        if (job.distance_miles === 0 || job.location.toLowerCase().includes("remote")) {
            distanceText = "💻 Remote";
        } else if (job.distance_miles !== null) {
            distanceText = `🚗 ${job.distance_miles.toFixed(1)} miles away`;
            if (job.distance_miles > 30) distanceClass += " critical";
            else if (job.distance_miles > 15) distanceClass += " warning";
        } else {
            distanceText = "📍 Unknown Distance";
        }
        
        // Formulate status button
        let statusButtonText = "Mark Applied";
        let statusClass = "btn-secondary";
        let nextStatus = "applied";
        if (job.status === "applied") {
            statusButtonText = "Applied ✅";
            statusClass = "btn-primary";
            nextStatus = "seen";
        }
        
        card.innerHTML = `
            <div class="job-card-header">
                <div class="title-area">
                    <h3>${job.title}</h3>
                    <div class="company-meta">
                        <strong>${job.company}</strong>
                        <span class="bullet-separator">•</span>
                        <span>${job.location}</span>
                        <span class="via-source">${job.via}</span>
                    </div>
                </div>
                <div class="badges-area">
                    <span class="badge ${distanceClass}">${distanceText}</span>
                    ${job.salary ? `<span class="badge badge-salary">💰 ${job.salary}</span>` : ''}
                    <span class="badge badge-posted">${job.posted_at || 'Recently posted'}</span>
                </div>
            </div>
            
            <div class="job-body">
                <p class="job-description" id="desc-${job.id}">${job.description}</p>
                <button class="btn-toggle-desc" onclick="toggleDescription('${job.id}', this)">Read More</button>
                
                ${job.notes ? `<div class="job-notes-preview"><strong>Notes:</strong> ${job.notes}</div>` : ''}
            </div>
            
            <div class="job-card-actions">
                <div class="action-buttons">
                    <button class="btn btn-sm ${statusClass}" onclick="updateJobStatus('${job.id}', '${nextStatus}')">
                        ${statusButtonText}
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="openNotesModal('${job.id}', '${job.title}', '${job.company}')">
                        📝 Notes
                    </button>
                    ${job.status !== 'archived' ? `
                        <button class="btn btn-sm btn-secondary" onclick="updateJobStatus('${job.id}', 'archived')">
                            📥 Archive
                        </button>
                    ` : `
                        <button class="btn btn-sm btn-secondary" onclick="updateJobStatus('${job.id}', 'new')">
                            📤 Restore
                        </button>
                    `}
                </div>
                <a href="${job.apply_link}" target="_blank" class="btn btn-sm btn-primary">
                    Apply Link ↗
                </a>
            </div>
        `;
        
        jobsListEl.appendChild(card);
    });
}

function toggleDescription(jobId, btn) {
    const descEl = document.getElementById(`desc-${jobId}`);
    if (descEl.classList.contains("expanded")) {
        descEl.classList.remove("expanded");
        btn.textContent = "Read More";
    } else {
        descEl.classList.add("expanded");
        btn.textContent = "Read Less";
    }
}

// ==========================================================================
// Modal Operations
// ==========================================================================
function openNotesModal(jobId, jobTitle, company) {
    modalJobId.value = jobId;
    modalJobTitle.textContent = `${jobTitle} at ${company}`;
    
    // Load notes value from local state
    const job = allJobs.find(j => j.id === jobId);
    modalNotesText.value = job ? (job.notes || "") : "";
    
    notesModal.classList.add("active");
}

function closeNotesModal() {
    notesModal.classList.remove("active");
}

// ==========================================================================
// Clipboard Operations
// ==========================================================================
function copyText(text, btnElement) {
    if (!text || text.includes("[FILL IN")) {
        alert("Please complete this field in profile_template.md first before copying!");
        return;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        const originalText = btnElement.textContent;
        btnElement.textContent = "Copied!";
        btnElement.classList.add("copied");
        
        setTimeout(() => {
            btnElement.textContent = originalText;
            btnElement.classList.remove("copied");
        }, 1500);
    }).catch(err => {
        console.error("Could not copy text: ", err);
    });
}
