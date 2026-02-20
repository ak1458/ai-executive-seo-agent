// SEO Executive Frontend App
const API_BASE = 'http://localhost:8000';

class App {
    constructor() {
        this.jobs = new Map();
        this.currentPage = 'dashboard';
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
        this.loadDashboard();
        this.loadWebsites();
        
        // Poll job status every 5 seconds
        setInterval(() => this.pollJobs(), 5000);
    }

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const page = e.currentTarget.dataset.page;
                this.navigate(page);
            });
        });

        // Auth button
        document.getElementById('authBtn').addEventListener('click', () => this.handleAuth());

        // Forms
        document.getElementById('auditForm').addEventListener('submit', (e) => this.handleAudit(e));
        document.getElementById('keywordForm').addEventListener('submit', (e) => this.handleKeywordResearch(e));
        document.getElementById('rankingForm').addEventListener('submit', (e) => this.handleRankCheck(e));
        document.getElementById('indexingForm').addEventListener('submit', (e) => this.handleIndexing(e));
        document.getElementById('indexingStatusForm').addEventListener('submit', (e) => this.handleIndexingCheck(e));
    }

    // Navigation
    navigate(page) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        
        document.getElementById(page).classList.add('active');
        document.querySelector(`[data-page="${page}"]`).classList.add('active');
        
        this.currentPage = page;
        
        // Refresh data based on page
        if (page === 'websites') this.loadWebsites();
    }

    // Auth
    async checkAuthStatus() {
        try {
            const response = await fetch(`${API_BASE}/auth/status`);
            const data = await response.json();
            
            this.updateAuthUI(data.google_authenticated);
        } catch (error) {
            console.error('Auth check failed:', error);
        }
    }

    updateAuthUI(isAuthenticated) {
        const statusBadge = document.getElementById('authStatus');
        const authBtn = document.getElementById('authBtn');
        
        if (isAuthenticated) {
            statusBadge.textContent = 'Connected';
            statusBadge.classList.add('connected');
            authBtn.textContent = 'Reconnect Google';
        } else {
            statusBadge.textContent = 'Not Connected';
            statusBadge.classList.remove('connected');
            authBtn.textContent = 'Connect Google';
        }
    }

    async handleAuth() {
        try {
            const response = await fetch(`${API_BASE}/auth/google`);
            const data = await response.json();
            
            if (data.auth_url) {
                window.open(data.auth_url, '_blank');
            }
        } catch (error) {
            alert('Failed to get auth URL: ' + error.message);
        }
    }

    // Dashboard
    async loadDashboard() {
        try {
            const websites = await fetch(`${API_BASE}/websites`).then(r => r.json());
            document.getElementById('websiteCount').textContent = websites.length;
        } catch (error) {
            document.getElementById('websiteCount').textContent = '0';
        }
        
        document.getElementById('keywordCount').textContent = '-';
        document.getElementById('auditCount').textContent = '-';
        document.getElementById('activeJobs').textContent = this.jobs.size;
    }

    // Websites
    async loadWebsites() {
        try {
            const response = await fetch(`${API_BASE}/websites`);
            const websites = await response.json();
            
            const tbody = document.getElementById('websitesTable');
            tbody.innerHTML = websites.map(w => `
                <tr>
                    <td>${w.url}</td>
                    <td>${w.gsc_property || '-'}</td>
                    <td>${new Date(w.created_at).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-secondary" onclick="app.deleteWebsite(${w.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Failed to load websites:', error);
        }
    }

    async deleteWebsite(id) {
        if (!confirm('Delete this website?')) return;
        
        try {
            await fetch(`${API_BASE}/websites/${id}`, { method: 'DELETE' });
            this.loadWebsites();
        } catch (error) {
            alert('Failed to delete: ' + error.message);
        }
    }

    showModal(type) {
        const modal = document.getElementById('modal');
        const body = document.getElementById('modalBody');
        
        if (type === 'addWebsite') {
            body.innerHTML = `
                <h3>Add Website</h3>
                <form id="addWebsiteForm" class="form">
                    <div class="form-group">
                        <label>Website URL</label>
                        <input type="url" id="newWebsiteUrl" placeholder="https://example.com" required>
                    </div>
                    <div class="form-group">
                        <label>GSC Property (optional)</label>
                        <input type="text" id="newWebsiteGsc" placeholder="https://example.com/">
                    </div>
                    <button type="submit" class="btn btn-primary">Add Website</button>
                </form>
            `;
            
            document.getElementById('addWebsiteForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.addWebsite();
            });
        }
        
        modal.classList.add('active');
    }

    hideModal() {
        document.getElementById('modal').classList.remove('active');
    }

    async addWebsite() {
        const url = document.getElementById('newWebsiteUrl').value;
        const gsc = document.getElementById('newWebsiteGsc').value;
        
        try {
            await fetch(`${API_BASE}/websites`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, gsc_property: gsc })
            });
            
            this.hideModal();
            this.loadWebsites();
            this.loadDashboard();
        } catch (error) {
            alert('Failed to add website: ' + error.message);
        }
    }

    // Tasks/Jobs
    async submitTask(taskType, params) {
        try {
            const response = await fetch(`${API_BASE}/task`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_type: taskType, params })
            });
            
            const data = await response.json();
            
            if (data.job_id) {
                this.jobs.set(data.job_id, { type: taskType, status: 'pending', result: null });
                this.updateJobPanel();
                return data.job_id;
            }
        } catch (error) {
            alert('Failed to submit task: ' + error.message);
        }
        return null;
    }

    async pollJobs() {
        for (const [jobId, job] of this.jobs) {
            if (job.status === 'complete' || job.status === 'error') continue;
            
            try {
                const response = await fetch(`${API_BASE}/task/${jobId}`);
                const data = await response.json();
                
                job.status = data.status;
                job.result = data.result;
                
                if (data.status === 'complete' || data.status === 'error') {
                    this.handleJobComplete(jobId, job);
                }
            } catch (error) {
                console.error('Job poll failed:', error);
            }
        }
        
        this.updateJobPanel();
        document.getElementById('activeJobs').textContent = 
            Array.from(this.jobs.values()).filter(j => j.status === 'pending' || j.status === 'running').length;
    }

    updateJobPanel() {
        const container = document.getElementById('jobList');
        
        if (this.jobs.size === 0) {
            container.innerHTML = '<p style="color: var(--text-light); font-size: 0.875rem;">No active jobs</p>';
            return;
        }
        
        container.innerHTML = Array.from(this.jobs).map(([id, job]) => `
            <div class="job-item">
                <span>${job.type}</span>
                <span class="job-status ${job.status}">${job.status}</span>
            </div>
        `).join('');
    }

    handleJobComplete(jobId, job) {
        // Could show notification or update UI
        console.log(`Job ${jobId} completed:`, job.result);
    }

    // Audit
    async handleAudit(e) {
        e.preventDefault();
        
        const url = document.getElementById('auditUrl').value;
        const maxPages = parseInt(document.getElementById('auditMaxPages').value);
        
        const jobId = await this.submitTask('full_audit', { url, max_pages: maxPages });
        
        if (jobId) {
            document.getElementById('auditResults').innerHTML = `
                <div class="result-item pending">
                    <p>Audit started (Job: ${jobId.slice(0, 8)}...)</p>
                    <p>Check the job panel for status</p>
                </div>
            `;
        }
    }

    // Keyword Research
    async handleKeywordResearch(e) {
        e.preventDefault();
        
        const seed = document.getElementById('seedKeyword').value;
        const location = document.getElementById('keywordLocation').value;
        const depth = parseInt(document.getElementById('keywordDepth').value);
        
        const locationCodes = { us: 2840, uk: 2826, ca: 2124, au: 2036 };
        
        const jobId = await this.submitTask('keyword_research', {
            seed,
            location_code: locationCodes[location],
            language_code: 'en',
            depth
        });
        
        if (jobId) {
            document.getElementById('keywordResults').innerHTML = `
                <div class="result-item pending">
                    <p>Research started (Job: ${jobId.slice(0, 8)}...)</p>
                    <p>This may take a few minutes...</p>
                </div>
            `;
        }
    }

    // Rank Check
    async handleRankCheck(e) {
        e.preventDefault();
        
        const domain = document.getElementById('rankingDomain').value;
        const keywordsText = document.getElementById('rankingKeywords').value;
        const locationCode = parseInt(document.getElementById('rankingLocation').value);
        
        const keywords = keywordsText.split('\n').map(k => k.trim()).filter(k => k);
        
        const jobId = await this.submitTask('rank_check', { domain, keywords, location_code: locationCode });
        
        if (jobId) {
            document.getElementById('rankingResults').innerHTML = `
                <div class="result-item pending">
                    <p>Rank check started (Job: ${jobId.slice(0, 8)}...)</p>
                    <p>Checking ${keywords.length} keywords...</p>
                </div>
            `;
        }
    }

    // Indexing
    async handleIndexing(e) {
        e.preventDefault();
        
        const urlsText = document.getElementById('indexingUrls').value;
        const urls = urlsText.split('\n').map(u => u.trim()).filter(u => u);
        
        if (urls.length > 200) {
            alert('Maximum 200 URLs per day allowed');
            return;
        }
        
        const jobId = await this.submitTask('submit_indexing', { urls });
        
        if (jobId) {
            document.getElementById('indexingQuota').innerHTML = `
                <p>Submitted ${urls.length} URLs for indexing</p>
                <p>Job: ${jobId.slice(0, 8)}...</p>
            `;
        }
    }

    async handleIndexingCheck(e) {
        e.preventDefault();
        
        const url = document.getElementById('checkUrl').value;
        
        try {
            const response = await fetch(`${API_BASE}/indexing/status?url=${encodeURIComponent(url)}`);
            const data = await response.json();
            
            document.getElementById('indexingStatusResult').innerHTML = `
                <div class="result-item ${data.error ? 'error' : 'success'}">
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                </div>
            `;
        } catch (error) {
            document.getElementById('indexingStatusResult').innerHTML = `
                <div class="result-item error">
                    <p>Error: ${error.message}</p>
                </div>
            `;
        }
    }
}

// Initialize app
const app = new App();

// Close modal on outside click
window.onclick = (e) => {
    const modal = document.getElementById('modal');
    if (e.target === modal) {
        app.hideModal();
    }
};
