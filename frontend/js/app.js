// GXO DockSchedule SPA Application Logic

const CONFIG = {
    apiBase: '/api'
};

// Automatic API Key injection for outgoing requests
const originalFetch = window.fetch;
window.fetch = async function (url, options = {}) {
    if (typeof url === 'string' && (url.startsWith('/api') || url.startsWith(CONFIG.apiBase))) {
        options.headers = options.headers || {};
        const apiKey = localStorage.getItem('api_key') || '';
        if (apiKey) {
            if (options.headers instanceof Headers) {
                options.headers.set('X-API-Key', apiKey);
            } else {
                options.headers['X-API-Key'] = apiKey;
            }
        }
    }
    return originalFetch(url, options);
};

// Global state
let state = {
    currentPath: '#/',
    metadata: {
        customers: [],
        carriers: [],
        productTypes: [],
        doors: [],
        operators: []
    }
};

// Start application
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch metadata first (lookup tables)
    await fetchMetadata();
    
    // 2. Setup router
    window.addEventListener('hashchange', handleRoute);
    handleRoute();
});

// Fetch lookup metadata from backend
async function fetchMetadata() {
    try {
        const res = await fetch(`${CONFIG.apiBase}/meta-data`);
        if (res.ok) {
            state.metadata = await res.json();
        }
    } catch (err) {
        console.error('Failed to load metadata', err);
    }
}

// Router
async function handleRoute() {
    const path = window.location.hash || '#/';
    state.currentPath = path;
    
    // Update active nav link
    updateNavigation(path);
    
    const appContainer = document.getElementById('app');
    appContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div></div>';
    
    // Close any open offcanvas sidebar on navigation (mobile layout)
    const offcanvasEl = document.getElementById('sidebarMenu');
    if (offcanvasEl) {
        const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
        if (bsOffcanvas) bsOffcanvas.hide();
    }

    try {
        if (path === '#/' || path === '#/dashboard') {
            await renderDashboard(appContainer);
        } else if (path === '#/appointments') {
            await renderAppointmentsList(appContainer);
        } else if (path === '#/add-appointment') {
            await renderAddAppointment(appContainer);
        } else if (path === '#/check-in') {
            await renderCheckIn(appContainer);
        } else if (path === '#/check-out') {
            await renderCheckOut(appContainer);
        } else if (path === '#/kpi-export') {
            await renderKPIExport(appContainer);
        } else if (path === '#/pit-board') {
            await renderPITBoard(appContainer);
        } else if (path === '#/admin') {
            await renderAdmin(appContainer);
        } else {
            appContainer.innerHTML = '<div class="alert alert-danger">Page not found</div>';
        }
    } catch (err) {
        console.error('Error rendering page', err);
        appContainer.innerHTML = `<div class="alert alert-danger">Error rendering page: ${err.message}</div>`;
    }
}

function updateNavigation(path) {
    const links = document.querySelectorAll('.sidebar-link');
    links.forEach(link => {
        const href = link.getAttribute('href');
        if (href === path || (path === '#/' && href === '#/') || (path === '#/dashboard' && href === '#/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Helper to format date
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

// Helper to format datetime
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '';
    const date = new Date(dateTimeStr);
    return date.toLocaleString([], { year: 'numeric', month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// ─── Dashboard View ─────────────────────────────────────────────────────────
async function renderDashboard(container) {
    const statsRes = await fetch(`${CONFIG.apiBase}/appointment-stats`);
    const stats = statsRes.ok ? await statsRes.json() : { total: 0, checked_in: 0, completed: 0, late: 0, missed: 0, ib_count: 0, ob_count: 0 };

    const checkedInRes = await fetch(`${CONFIG.apiBase}/appointments?status=Checked In`);
    const checkedIn = checkedInRes.ok ? (await checkedInRes.json()).appointments : [];

    container.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">Overview</span>
                <h1 class="operations-header-serif">Dashboard</h1>
            </div>
            <div class="col-auto">
                <span class="badge bg-dark fs-6">${new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</span>
            </div>
        </div>

        <!-- Stats Cards Grid -->
        <div class="row g-3 mb-5">
            <div class="col-6 col-md-4 col-lg-2">
                <div class="premium-kpi-card card">
                    <span class="kpi-label">Scheduled</span>
                    <h3 class="kpi-value text-primary mono">${stats.total}</h3>
                    <span class="kpi-subtext">Total Appts</span>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="premium-kpi-card card">
                    <span class="kpi-label">Checked In</span>
                    <h3 class="kpi-value text-warning mono">${stats.checked_in}</h3>
                    <span class="kpi-subtext">At Facility</span>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="premium-kpi-card card">
                    <span class="kpi-label">Completed</span>
                    <h3 class="kpi-value text-success mono">${stats.completed}</h3>
                    <span class="kpi-subtext">Checked Out</span>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="premium-kpi-card card">
                    <span class="kpi-label">Late</span>
                    <h3 class="kpi-value text-danger mono">${stats.late}</h3>
                    <span class="kpi-subtext">>15 min Late</span>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="premium-kpi-card card">
                    <span class="kpi-label">Missed</span>
                    <h3 class="kpi-value text-secondary mono">${stats.missed}</h3>
                    <span class="kpi-subtext">No Show</span>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="premium-kpi-card card">
                    <span class="kpi-label">IB / OB</span>
                    <h3 class="kpi-value text-dark mono">${stats.ib_count}/${stats.ob_count}</h3>
                    <span class="kpi-subtext">Split</span>
                </div>
            </div>
        </div>

        <!-- Quick Action Buttons -->
        <h4 class="mb-3 text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.08em;">Quick Actions</h4>
        <div class="row g-3 mb-5">
            <div class="col-6 col-md-3">
                <a href="#/add-appointment" class="btn btn-secondary w-100 py-3 d-flex flex-column align-items-center justify-content-center text-decoration-none">
                    <i class="bi bi-calendar-plus text-primary fs-3 mb-2"></i>
                    <span class="fw-semibold">Add Appt</span>
                </a>
            </div>
            <div class="col-6 col-md-3">
                <a href="#/check-in" class="btn btn-secondary w-100 py-3 d-flex flex-column align-items-center justify-content-center text-decoration-none">
                    <i class="bi bi-box-arrow-in-right text-warning fs-3 mb-2"></i>
                    <span class="fw-semibold">Check-In</span>
                </a>
            </div>
            <div class="col-6 col-md-3">
                <a href="#/check-out" class="btn btn-secondary w-100 py-3 d-flex flex-column align-items-center justify-content-center text-decoration-none">
                    <i class="bi bi-box-arrow-left text-success fs-3 mb-2"></i>
                    <span class="fw-semibold">Check-Out</span>
                </a>
            </div>
            <div class="col-6 col-md-3">
                <a href="#/kpi-export" class="btn btn-secondary w-100 py-3 d-flex flex-column align-items-center justify-content-center text-decoration-none">
                    <i class="bi bi-file-earmark-spreadsheet text-info fs-3 mb-2"></i>
                    <span class="fw-semibold">KPI Export</span>
                </a>
            </div>
        </div>

        <!-- Active Operations (Checked-In Drivers) -->
        <div class="card mb-4">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <span><i class="bi bi-truck me-2"></i>Checked-In Drivers (At Facility)</span>
                <span class="badge bg-warning text-dark rounded-pill">${checkedIn.length} Active</span>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>BOL/Shipment</th>
                                <th>Customer</th>
                                <th>Carrier</th>
                                <th>Trailer</th>
                                <th>Door</th>
                                <th>Operator</th>
                                <th>Check-In Time</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${checkedIn.length === 0 ? `
                                <tr>
                                    <td colspan="9" class="text-center text-muted py-4">
                                        <i class="bi bi-info-circle fs-4 d-block mb-2"></i>
                                        No drivers currently checked in.
                                    </td>
                                </tr>
                            ` : checkedIn.map(appt => `
                                <tr>
                                    <td><span class="badge ${appt.appt_type === 'IB' ? 'bg-primary' : 'bg-info'}">${appt.appt_type}</span></td>
                                    <td class="mono font-semibold">${appt.bol_shipment_no || 'N/A'}</td>
                                    <td>${appt.customer || 'N/A'}</td>
                                    <td>${appt.carrier || 'N/A'}</td>
                                    <td class="mono">${appt.trailer_no || 'N/A'}</td>
                                    <td><span class="badge bg-secondary">${appt.door_name || 'Unassigned'}</span></td>
                                    <td>${appt.pit_operator || 'Unassigned'}</td>
                                    <td class="mono">${formatDateTime(appt.check_in_time)}</td>
                                    <td><span class="badge bg-warning">${appt.status}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

// ─── Appointments List View ──────────────────────────────────────────────────
async function renderAppointmentsList(container) {
    // 1. Render layout with search controls
    container.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">Log</span>
                <h1 class="operations-header-serif">Appointments List</h1>
            </div>
        </div>

        <div class="card mb-4">
            <div class="card-body">
                <form id="filter-form" class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">Search</label>
                        <input type="text" name="search" class="form-control" placeholder="BOL, Carrier, Trailer...">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Date From</label>
                        <input type="date" name="date_from" class="form-control">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Date To</label>
                        <input type="date" name="date_to" class="form-control">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Type</label>
                        <select name="appt_type" class="form-select">
                            <option value="">All</option>
                            <option value="IB">Inbound</option>
                            <option value="OB">Outbound</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Status</label>
                        <select name="status" class="form-select">
                            <option value="">All</option>
                            <option value="Scheduled">Scheduled</option>
                            <option value="Checked In">Checked In</option>
                            <option value="Completed">Completed</option>
                            <option value="Late">Late</option>
                            <option value="Missed">Missed</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </div>
                    <div class="col-12 text-end">
                        <button type="submit" class="btn btn-primary btn-sm"><i class="bi bi-funnel"></i> Apply Filters</button>
                        <button type="reset" class="btn btn-secondary btn-sm"><i class="bi bi-x-circle"></i> Clear</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="card">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0" id="appointments-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Date/Time</th>
                                <th>BOL</th>
                                <th>Customer</th>
                                <th>Carrier</th>
                                <th>Visitor</th>
                                <th>Trailer</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="appointments-list-body">
                            <!-- Injected by API -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    const filterForm = document.getElementById('filter-form');
    filterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await loadAppointments();
    });
    filterForm.addEventListener('reset', () => {
        setTimeout(loadAppointments, 50);
    });

    // Load initial list
    await loadAppointments();

    async function loadAppointments() {
        const tbody = document.getElementById('appointments-list-body');
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> Loading...</td></tr>';

        const formData = new FormData(filterForm);
        const params = new URLSearchParams();
        for (const [key, val] of formData.entries()) {
            if (val) params.append(key, val);
        }

        const res = await fetch(`${CONFIG.apiBase}/appointments?${params.toString()}`);
        if (res.ok) {
            const data = await res.json();
            const list = data.appointments;
            if (list.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No appointments found matching filters.</td></tr>';
            } else {
                tbody.innerHTML = list.map(appt => `
                    <tr>
                        <td><span class="badge ${appt.appt_type === 'IB' ? 'bg-primary' : 'bg-info'}">${appt.appt_type}</span></td>
                        <td class="mono fw-semibold">${formatDateTime(appt.scheduled_datetime)}</td>
                        <td class="mono">${appt.bol_shipment_no || 'N/A'}</td>
                        <td>${appt.customer || 'N/A'}</td>
                        <td>${appt.carrier || 'N/A'}</td>
                        <td>${appt.visitor_name || 'N/A'}</td>
                        <td class="mono">${appt.trailer_no || 'N/A'}</td>
                        <td>
                            <span class="badge ${
                                appt.status === 'Completed' ? 'bg-success' :
                                appt.status === 'Checked In' || appt.status === 'Early' || appt.status === 'On Time' || appt.status === 'Late' ? 'bg-warning text-dark' :
                                appt.status === 'Cancelled' || appt.status === 'Missed' ? 'bg-danger' : 'bg-secondary'
                            }">${appt.status}</span>
                        </td>
                    </tr>
                `).join('');
            }
        } else {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger py-4">Error loading appointments.</td></tr>';
        }
    }
}

// ─── Add Appointment View ────────────────────────────────────────────────────
async function renderAddAppointment(container) {
    container.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">Scheduling</span>
                <h1 class="operations-header-serif">Add Appointment</h1>
            </div>
        </div>

        <div class="card max-width-800 mx-auto">
            <div class="card-body">
                <form id="add-appt-form">
                    <div id="warnings-container"></div>
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label">Appointment Type</label>
                            <select name="appt_type" id="appt_type" class="form-select" required>
                                <option value="IB">Inbound</option>
                                <option value="OB">Outbound</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">BOL / Shipment No</label>
                            <input type="text" name="bol_shipment_no" id="bol_shipment_no" class="form-control" placeholder="Enter BOL number" required>
                            <div class="form-text text-danger d-none" id="bol-warning">BOL already exists in system!</div>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Scheduled Date</label>
                            <input type="date" name="appt_date" id="appt_date" class="form-control" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Scheduled Time</label>
                            <input type="time" name="appt_time" id="appt_time" class="form-control" required>
                            <div class="form-text text-danger d-none" id="capacity-warning">Selected slot is at capacity!</div>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Customer</label>
                            <select name="customer_id" class="form-select" required>
                                <option value="">Select Customer</option>
                                ${state.metadata.customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Carrier</label>
                            <select name="carrier_id" class="form-select" required>
                                <option value="">Select Carrier</option>
                                ${state.metadata.carriers.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Product Type</label>
                            <select name="product_type_id" class="form-select" required>
                                <option value="">Select Product Type</option>
                                ${state.metadata.productTypes.map(pt => `<option value="${pt.id}">${pt.name}</option>`).join('')}
                            </select>
                        </div>
                        <div class="col-12">
                            <label class="form-label">Delivery No (Optional)</label>
                            <input type="text" name="delivery_no" class="form-control" placeholder="Enter delivery number">
                        </div>
                        <div class="col-12">
                            <label class="form-label">Notes (Optional)</label>
                            <textarea name="notes" class="form-control" rows="3" placeholder="Enter notes..."></textarea>
                        </div>
                        <div class="col-12 text-end">
                            <button type="submit" class="btn btn-success"><i class="bi bi-check-circle"></i> Create Appointment</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    `;

    const form = document.getElementById('add-appt-form');
    const bolInput = document.getElementById('bol_shipment_no');
    const dateInput = document.getElementById('appt_date');
    const timeInput = document.getElementById('appt_time');
    const typeSelect = document.getElementById('appt_type');

    // Default to today's date
    dateInput.value = new Date().toISOString().split('T')[0];

    // Check duplicate BOL
    bolInput.addEventListener('blur', async () => {
        const bol = bolInput.value.trim();
        const warning = document.getElementById('bol-warning');
        if (!bol) {
            warning.classList.add('d-none');
            return;
        }
        const res = await fetch(`${CONFIG.apiBase}/check-bol?bol=${encodeURIComponent(bol)}`);
        if (res.ok) {
            const data = await res.json();
            if (data.exists) {
                warning.classList.remove('d-none');
            } else {
                warning.classList.add('d-none');
            }
        }
    });

    // Check slot capacity
    const checkCapacity = async () => {
        const date = dateInput.value;
        const time = timeInput.value;
        const type = typeSelect.value;
        const warning = document.getElementById('capacity-warning');

        if (!date || !time) {
            warning.classList.add('d-none');
            return;
        }

        const res = await fetch(`${CONFIG.apiBase}/capacity-check?date=${date}&time=${time}&appt_type=${type}`);
        if (res.ok) {
            const data = await res.json();
            if (data.at_capacity) {
                warning.classList.remove('d-none');
                warning.textContent = `Selected slot is at capacity (${data.existing}/${data.max_capacity} appointments scheduled)!`;
            } else {
                warning.classList.add('d-none');
            }
        }
    };

    dateInput.addEventListener('change', checkCapacity);
    timeInput.addEventListener('change', checkCapacity);
    typeSelect.addEventListener('change', checkCapacity);

    // Form submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {};
        new FormData(form).forEach((value, key) => data[key] = value);

        const res = await fetch(`${CONFIG.apiBase}/appointments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            window.location.hash = '#/appointments';
        } else {
            const err = await res.json();
            document.getElementById('warnings-container').innerHTML = `
                <div class="alert alert-danger">${err.error || 'Failed to create appointment'}</div>
            `;
        }
    });
}

// ─── Check-In View ──────────────────────────────────────────────────────────
async function renderCheckIn(container) {
    container.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">Logistics</span>
                <h1 class="operations-header-serif">Driver Check-In</h1>
            </div>
        </div>

        <div class="card mb-4 max-width-800 mx-auto">
            <div class="card-body">
                <h5 class="card-title mb-3">BOL Lookup</h5>
                <form id="check-in-lookup-form" class="input-group input-group-lg">
                    <input type="text" id="lookup-bol" class="form-control" placeholder="Search Scheduled BOL No..." required>
                    <button type="submit" class="btn btn-primary"><i class="bi bi-search"></i> Find</button>
                </form>
            </div>
        </div>

        <div id="check-in-content-container" class="max-width-800 mx-auto"></div>
    `;

    const lookupForm = document.getElementById('check-in-lookup-form');
    lookupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const bol = document.getElementById('lookup-bol').value.trim();
        await performBOLSearch(bol);
    });

    async function performBOLSearch(bol) {
        const contentDiv = document.getElementById('check-in-content-container');
        contentDiv.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></div>';

        const res = await fetch(`${CONFIG.apiBase}/appointments?q=${encodeURIComponent(bol)}&status=Scheduled`);
        if (res.ok) {
            const data = await res.json();
            const matches = data.appointments;
            
            if (matches.length === 0) {
                contentDiv.innerHTML = `
                    <div class="alert alert-warning text-center">
                        <i class="bi bi-exclamation-triangle fs-4 d-block mb-2"></i>
                        No scheduled appointments found for BOL <strong>${bol}</strong>.
                    </div>
                `;
            } else if (matches.length === 1) {
                renderCheckInForm(contentDiv, matches[0]);
            } else {
                renderBOLSelection(contentDiv, matches);
            }
        } else {
            contentDiv.innerHTML = '<div class="alert alert-danger">Error fetching appointment matches.</div>';
        }
    }

    function renderBOLSelection(container, matches) {
        container.innerHTML = `
            <div class="card">
                <div class="card-header bg-warning text-dark">Multiple Matches Found</div>
                <div class="card-body">
                    <p class="text-muted">Select the scheduled appointment you wish to check in:</p>
                    <div class="list-group">
                        ${matches.map(m => `
                            <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center select-appt-btn" data-id="${m.id}">
                                <div>
                                    <span class="badge bg-secondary me-2">${m.appt_type}</span>
                                    <strong>${m.bol_shipment_no || 'N/A'}</strong> - ${m.customer}
                                </div>
                                <span class="mono text-muted small">${formatDateTime(m.appt_date + 'T' + m.appt_time)}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        container.querySelectorAll('.select-appt-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.getAttribute('data-id');
                const matched = matches.find(m => m.id == id);
                renderCheckInForm(container, matched);
            });
        });
    }

    function renderCheckInForm(container, appt) {
        container.innerHTML = `
            <div class="card">
                <div class="card-header bg-success text-white">
                    <i class="bi bi-box-arrow-in-right me-2"></i>Check-In Details: BOL ${appt.bol_shipment_no}
                </div>
                <div class="card-body">
                    <form id="check-in-form-submit">
                        <input type="hidden" name="appointment_id" value="${appt.id}">
                        
                        <div class="alert alert-light border mb-4">
                            <div class="row g-2">
                                <div class="col-6 col-sm-3"><strong>Type:</strong> ${appt.appt_type}</div>
                                <div class="col-6 col-sm-3"><strong>Date:</strong> ${formatDate(appt.appt_date)}</div>
                                <div class="col-6 col-sm-3"><strong>Time:</strong> ${appt.appt_time}</div>
                                <div class="col-6 col-sm-3"><strong>Customer:</strong> ${appt.customer}</div>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label">Visitor Name</label>
                                <input type="text" name="visitor_name" class="form-control" placeholder="Driver Full Name" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Trailer No</label>
                                <input type="text" name="trailer_no" class="form-control" placeholder="Enter trailer no" required>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">License State</label>
                                <input type="text" name="drivers_license_state" class="form-control" placeholder="e.g. MN" required>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Load Lock</label>
                                <select name="load_lock" class="form-select" required>
                                    <option value="Y">Yes</option>
                                    <option value="N">No</option>
                                    <option value="NA">N/A</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Assigned Door</label>
                                <select name="assigned_door_id" class="form-select" required>
                                    <option value="">Select Door</option>
                                    ${state.metadata.doors.filter(d => d.status === 'Open').map(d => `<option value="${d.id}">${d.door_name} (${d.direction})</option>`).join('')}
                                </select>
                            </div>
                            <div class="col-md-12">
                                <label class="form-label">PIT Operator</label>
                                <select name="pit_operator_id" class="form-select" required>
                                    <option value="">Select Operator</option>
                                    ${state.metadata.operators.map(op => `<option value="${op.id}">${op.name}</option>`).join('')}
                                </select>
                            </div>
                            <div class="col-12">
                                <label class="form-label">Notes (Optional)</label>
                                <textarea name="notes" class="form-control" rows="2" placeholder="Arrival comments..."></textarea>
                            </div>
                            <div class="col-12 text-end mt-4">
                                <button type="submit" class="btn btn-primary"><i class="bi bi-box-arrow-in-right"></i> Complete Check-In</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.getElementById('check-in-form-submit').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formObj = {};
            new FormData(e.target).forEach((v, k) => formObj[k] = v);

            const res = await fetch(`${CONFIG.apiBase}/check-in`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formObj)
            });

            if (res.ok) {
                window.location.hash = '#/dashboard';
            } else {
                const err = await res.json();
                alert(`Check-in failed: ${err.error || 'Unknown error'}`);
            }
        });
    }
}

// ─── Check-Out View ─────────────────────────────────────────────────────────
async function renderCheckOut(container) {
    container.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">Logistics</span>
                <h1 class="operations-header-serif">Driver Check-Out</h1>
            </div>
        </div>

        <div class="card mb-4 max-width-800 mx-auto">
            <div class="card-body">
                <h5 class="card-title mb-3">Checked-In BOL Lookup</h5>
                <form id="check-out-lookup-form" class="input-group input-group-lg">
                    <input type="text" id="checkout-bol" class="form-control" placeholder="Search BOL of Checked-in Driver..." required>
                    <button type="submit" class="btn btn-primary"><i class="bi bi-search"></i> Find</button>
                </form>
            </div>
        </div>

        <div id="check-out-content-container" class="max-width-800 mx-auto"></div>
    `;

    const lookupForm = document.getElementById('check-out-lookup-form');
    lookupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const bol = document.getElementById('checkout-bol').value.trim();
        await performCheckoutBOLSearch(bol);
    });

    async function performCheckoutBOLSearch(bol) {
        const contentDiv = document.getElementById('check-out-content-container');
        contentDiv.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></div>';

        const res = await fetch(`${CONFIG.apiBase}/appointments?q=${encodeURIComponent(bol)}&status=Checked In`);
        if (res.ok) {
            const data = await res.json();
            const matches = data.appointments;
            
            if (matches.length === 0) {
                contentDiv.innerHTML = `
                    <div class="alert alert-warning text-center">
                        <i class="bi bi-exclamation-triangle fs-4 d-block mb-2"></i>
                        No checked-in drivers found for BOL <strong>${bol}</strong>.
                    </div>
                `;
            } else if (matches.length === 1) {
                renderCheckOutForm(contentDiv, matches[0]);
            } else {
                renderCheckoutBOLSelection(contentDiv, matches);
            }
        } else {
            contentDiv.innerHTML = '<div class="alert alert-danger">Error fetching appointment matches.</div>';
        }
    }

    function renderCheckoutBOLSelection(container, matches) {
        container.innerHTML = `
            <div class="card">
                <div class="card-header bg-warning text-dark">Multiple Matches Found</div>
                <div class="card-body">
                    <p class="text-muted">Select the driver you wish to check out:</p>
                    <div class="list-group">
                        ${matches.map(m => `
                            <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center select-checkout-appt-btn" data-id="${m.id}">
                                <div>
                                    <span class="badge bg-warning text-dark me-2">${m.status}</span>
                                    <strong>${m.bol_shipment_no || 'N/A'}</strong> - ${m.customer}
                                </div>
                                <span class="mono text-muted small">${m.visitor_name || 'N/A'} (${m.trailer_no || 'No Trailer'})</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        container.querySelectorAll('.select-checkout-appt-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-id');
                const matched = matches.find(m => m.id == id);
                renderCheckOutForm(container, matched);
            });
        });
    }

    function renderCheckOutForm(container, appt) {
        container.innerHTML = `
            <div class="card">
                <div class="card-header bg-danger text-white">
                    <i class="bi bi-box-arrow-left me-2"></i>Check-Out: BOL ${appt.bol_shipment_no}
                </div>
                <div class="card-body">
                    <form id="check-out-form-submit">
                        <input type="hidden" name="appointment_id" value="${appt.id}">
                        
                        <div class="alert alert-light border mb-4">
                            <div class="row g-2">
                                <div class="col-6 col-sm-3"><strong>Driver:</strong> ${appt.visitor_name || 'N/A'}</div>
                                <div class="col-6 col-sm-3"><strong>Trailer:</strong> ${appt.trailer_no || 'N/A'}</div>
                                <div class="col-6 col-sm-3"><strong>Door:</strong> ${appt.door_name || 'Unassigned'}</div>
                                <div class="col-6 col-sm-3"><strong>Check-In:</strong> ${formatDateTime(appt.check_in_time)}</div>
                            </div>
                        </div>

                        <div class="row g-3">
                            <div class="col-12">
                                <label class="form-label">Notes (Optional)</label>
                                <textarea name="notes" class="form-control" rows="3" placeholder="Departure comments, load seal info..."></textarea>
                            </div>
                            <div class="col-12 text-end mt-4">
                                <button type="submit" class="btn btn-danger"><i class="bi bi-box-arrow-left"></i> Confirm Check-Out</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.getElementById('check-out-form-submit').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formObj = {};
            new FormData(e.target).forEach((v, k) => formObj[k] = v);

            const res = await fetch(`${CONFIG.apiBase}/check-out`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formObj)
            });

            if (res.ok) {
                window.location.hash = '#/dashboard';
            } else {
                const err = await res.json();
                alert(`Check-out failed: ${err.error || 'Unknown error'}`);
            }
        });
    }
}

// ─── KPI Export View ────────────────────────────────────────────────────────
async function renderKPIExport(container) {
    container.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">Reporting</span>
                <h1 class="operations-header-serif">KPI Export</h1>
            </div>
        </div>

        <div class="card mb-4">
            <div class="card-body">
                <form id="kpi-form" class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">Date From</label>
                        <input type="date" name="date_from" id="kpi_date_from" class="form-control" required>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Date To</label>
                        <input type="date" name="date_to" id="kpi_date_to" class="form-control" required>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Appt Type</label>
                        <select name="appt_type" class="form-select">
                            <option value="All">All</option>
                            <option value="IB">Inbound</option>
                            <option value="OB">Outbound</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Status</label>
                        <select name="status" class="form-select">
                            <option value="All">All</option>
                            <option value="Scheduled">Scheduled</option>
                            <option value="Checked In">Checked In</option>
                            <option value="Completed">Completed</option>
                            <option value="Late">Late</option>
                            <option value="Missed">Missed</option>
                        </select>
                    </div>
                    
                    <div class="col-12 mt-3">
                        <label class="form-label d-block">Inclusion Flags</label>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" name="include_scheduled" id="inc_sch" value="true" checked>
                            <label class="form-check-label" for="inc_sch">Scheduled</label>
                        </div>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" name="include_checked_in" id="inc_ci" value="true" checked>
                            <label class="form-check-label" for="inc_ci">Checked In / Active</label>
                        </div>
                        <div class="form-check form-check-inline">
                            <input class="form-check-input" type="checkbox" name="include_completed" id="inc_cmp" value="true" checked>
                            <label class="form-check-label" for="inc_cmp">Completed</label>
                        </div>
                    </div>

                    <div class="col-12 text-end mt-4">
                        <button type="submit" class="btn btn-primary"><i class="bi bi-eye"></i> Preview Export</button>
                        <button type="button" id="copy-btn" class="btn btn-warning"><i class="bi bi-clipboard"></i> Copy to Clipboard</button>
                        <button type="button" id="download-btn" class="btn btn-info text-white"><i class="bi bi-download"></i> Download CSV</button>
                    </div>
                </form>
            </div>
        </div>

        <div id="kpi-preview-container"></div>
    `;

    // Default dates (yesterday and today)
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);
    
    document.getElementById('kpi_date_from').value = yesterday.toISOString().split('T')[0];
    document.getElementById('kpi_date_to').value = today.toISOString().split('T')[0];

    const form = document.getElementById('kpi-form');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await loadPreview();
    });

    document.getElementById('copy-btn').addEventListener('click', async () => {
        const params = getFilterParams();
        params.append('format', 'tsv');

        const res = await fetch(`${CONFIG.apiBase}/kpi-export?${params.toString()}`);
        if (res.ok) {
            const data = await res.json();
            try {
                await navigator.clipboard.writeText(data.tsv);
                alert('TSV copied to clipboard! Ready to paste into Excel.');
            } catch (err) {
                alert('Failed to copy to clipboard automatically. Please copy the text manually.');
            }
        } else {
            alert('Failed to generate export file.');
        }
    });

    document.getElementById('download-btn').addEventListener('click', () => {
        const params = getFilterParams();
        params.append('format', 'csv');
        window.open(`${CONFIG.apiBase}/kpi-export?${params.toString()}`, '_blank');
    });

    function getFilterParams() {
        const formData = new FormData(form);
        const params = new URLSearchParams();
        for (const [k, v] of formData.entries()) {
            params.append(k, v);
        }
        return params;
    }

    async function loadPreview() {
        const previewDiv = document.getElementById('kpi-preview-container');
        previewDiv.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div></div>';

        const params = getFilterParams();
        params.append('format', 'json');

        const res = await fetch(`${CONFIG.apiBase}/kpi-export?${params.toString()}`);
        if (res.ok) {
            const data = await res.json();
            const columns = data.columns;
            const rows = data.rows;

            if (rows.length === 0) {
                previewDiv.innerHTML = '<div class="alert alert-light border text-center">No rows matched the criteria.</div>';
                return;
            }

            previewDiv.innerHTML = `
                <div class="card">
                    <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                        <span>Preview Export (${rows.length} rows)</span>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                            <table class="table table-striped table-hover mb-0 kpi-preview">
                                <thead>
                                    <tr>
                                        ${columns.map(c => `<th>${c}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${rows.map(row => `
                                        <tr>
                                            ${row.map(val => `<td>${val === null ? '' : val}</td>`).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } else {
            previewDiv.innerHTML = '<div class="alert alert-danger">Error generating preview.</div>';
        }
    }
}

// ─── PIT Board App View ──────────────────────────────────────────────────────
async function renderPITBoard(container) {
    container.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">Logistics Board</span>
                <h1 class="operations-header-serif"><i class="bi bi-forklift me-2"></i>PIT Operations Board</h1>
            </div>
            <div class="col-auto">
                <button id="refresh-pit" class="btn btn-secondary btn-sm"><i class="bi bi-arrow-clockwise"></i> Refresh</button>
            </div>
        </div>

        <div class="row g-4" id="pit-doors-grid">
            <!-- Populated via API -->
        </div>
    `;

    document.getElementById('refresh-pit').addEventListener('click', loadPITBoard);
    await loadPITBoard();

    async function loadPITBoard() {
        const grid = document.getElementById('pit-doors-grid');
        grid.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-primary" role="status"></div></div>';

        const res = await fetch(`${CONFIG.apiBase}/appointments?status=Checked In`);
        if (res.ok) {
            const data = await res.json();
            const activeAppts = data.appointments;

            // Map visits to door
            const doorMap = {};
            activeAppts.forEach(appt => {
                if (appt.door_name) {
                    doorMap[appt.door_name] = appt;
                }
            });

            // Make sure all open/active doors are rendered
            const doors = state.metadata.doors;
            
            grid.innerHTML = doors.map(door => {
                const activeVisit = doorMap[door.door_name];
                
                let borderClass = 'border-start-secondary';
                let statusBadge = `<span class="badge bg-secondary">${door.status}</span>`;
                
                if (door.status === 'Occupied' || activeVisit) {
                    borderClass = 'border-start-danger';
                    statusBadge = `<span class="badge bg-danger">Occupied</span>`;
                } else if (door.status === 'Open') {
                    borderClass = 'border-start-success';
                    statusBadge = `<span class="badge bg-success">Open</span>`;
                }

                return `
                    <div class="col-md-6 col-lg-4">
                        <div class="card h-100 ${borderClass}" style="border-left-width: 5px !important;">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <h4 class="mb-0 font-serif">${door.door_name}</h4>
                                    ${statusBadge}
                                </div>
                                <p class="text-muted small mb-2"><i class="bi bi-compass"></i> Area: ${door.area || 'Main Dock'} | Type: ${door.direction}</p>
                                
                                ${activeVisit ? `
                                    <div class="p-3 bg-light rounded mt-3">
                                        <div class="d-flex justify-content-between mb-1">
                                            <span class="fw-bold">${activeVisit.customer}</span>
                                            <span class="badge bg-primary">${activeVisit.appt_type}</span>
                                        </div>
                                        <div class="mono small text-muted mb-2">BOL: ${activeVisit.bol_shipment_no}</div>
                                        <hr class="my-2">
                                        <div class="small"><strong>Driver:</strong> ${activeVisit.visitor_name || 'N/A'}</div>
                                        <div class="small"><strong>Trailer:</strong> ${activeVisit.trailer_no || 'N/A'}</div>
                                        <div class="small mt-2"><strong>Operator:</strong> <span class="badge bg-secondary">${activeVisit.pit_operator || 'Unassigned'}</span></div>
                                    </div>
                                ` : `
                                    <div class="text-center py-4 text-muted small bg-light rounded mt-3">
                                        No active driver assigned
                                    </div>
                                `}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            grid.innerHTML = '<div class="col-12 alert alert-danger">Error loading PIT board.</div>';
        }
    }
}

// ─── Admin View ─────────────────────────────────────────────────────────────
async function renderAdmin(container) {
    // Refresh metadata first to ensure current state
    await fetchMetadata();

    container.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">System Settings</span>
                <h1 class="operations-header-serif"><i class="bi bi-gear me-2"></i>Administration Panel</h1>
            </div>
        </div>

        <div class="row g-4">
            <!-- 1. Customers Management -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header bg-dark text-white fw-bold">Manage Customers</div>
                    <div class="card-body">
                        <form id="add-customer-form" class="input-group mb-3">
                            <input type="text" id="cust-name" class="form-control form-control-sm" placeholder="New Customer Name" required>
                            <button type="submit" class="btn btn-sm btn-primary">Add</button>
                        </form>
                        <div style="max-height: 250px; overflow-y: auto;">
                            <ul class="list-group list-group-flush">
                                ${state.metadata.customers.map(c => `
                                    <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                                        <span>${c.name}</span>
                                        <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-entity-btn" data-entity="customer" data-id="${c.id}">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </li>
                                `).join('')}
                                ${state.metadata.customers.length === 0 ? '<li class="list-group-item text-muted text-center py-3">No customers</li>' : ''}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 2. Carriers Management -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header bg-dark text-white fw-bold">Manage Carriers</div>
                    <div class="card-body">
                        <form id="add-carrier-form" class="input-group mb-3">
                            <input type="text" id="carr-name" class="form-control form-control-sm" placeholder="New Carrier Name" required>
                            <button type="submit" class="btn btn-sm btn-primary">Add</button>
                        </form>
                        <div style="max-height: 250px; overflow-y: auto;">
                            <ul class="list-group list-group-flush">
                                ${state.metadata.carriers.map(c => `
                                    <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                                        <span>${c.name}</span>
                                        <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-entity-btn" data-entity="carrier" data-id="${c.id}">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </li>
                                `).join('')}
                                ${state.metadata.carriers.length === 0 ? '<li class="list-group-item text-muted text-center py-3">No carriers</li>' : ''}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 3. Doors Management -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header bg-dark text-white fw-bold">Manage Doors</div>
                    <div class="card-body">
                        <form id="add-door-form" class="row g-2 mb-3">
                            <div class="col-6">
                                <input type="text" id="door-name" class="form-control form-control-sm" placeholder="Door Name (e.g. Door 5)" required>
                            </div>
                            <div class="col-6">
                                <select id="door-dir" class="form-select form-select-sm" required>
                                    <option value="IB">Inbound</option>
                                    <option value="OB">Outbound</option>
                                    <option value="Both">Both</option>
                                </select>
                            </div>
                            <div class="col-12 text-end">
                                <button type="submit" class="btn btn-sm btn-primary w-100">Add Door</button>
                            </div>
                        </form>
                        <div style="max-height: 250px; overflow-y: auto;">
                            <ul class="list-group list-group-flush">
                                ${state.metadata.doors.map(d => `
                                    <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                                        <div>
                                            <strong>${d.door_name}</strong> 
                                            <span class="badge bg-secondary ms-2">${d.direction}</span>
                                            <span class="badge ${d.status === 'Open' ? 'bg-success' : 'bg-danger'} ms-1">${d.status}</span>
                                        </div>
                                        <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-entity-btn" data-entity="door" data-id="${d.id}">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </li>
                                `).join('')}
                                ${state.metadata.doors.length === 0 ? '<li class="list-group-item text-muted text-center py-3">No doors</li>' : ''}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 4. PIT Operators Management -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header bg-dark text-white fw-bold">Manage PIT Operators</div>
                    <div class="card-body">
                        <form id="add-operator-form" class="row g-2 mb-3">
                            <div class="col-8">
                                <input type="text" id="op-name" class="form-control form-control-sm" placeholder="Operator Name" required>
                            </div>
                            <div class="col-4">
                                <input type="text" id="op-initials" class="form-control form-control-sm" placeholder="Initials" required>
                            </div>
                            <div class="col-12">
                                <button type="submit" class="btn btn-sm btn-primary w-100">Add Operator</button>
                            </div>
                        </form>
                        <div style="max-height: 250px; overflow-y: auto;">
                            <ul class="list-group list-group-flush">
                                ${state.metadata.operators.map(op => `
                                    <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                                        <span>${op.name} (${op.initials})</span>
                                        <button class="btn btn-sm btn-outline-danger py-0 px-1 delete-entity-btn" data-entity="operator" data-id="${op.id}">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </li>
                                `).join('')}
                                ${state.metadata.operators.length === 0 ? '<li class="list-group-item text-muted text-center py-3">No operators</li>' : ''}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Event Handlers for forms
    document.getElementById('add-customer-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('cust-name').value.trim();
        await addEntity('customer', { name });
    });

    document.getElementById('add-carrier-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('carr-name').value.trim();
        await addEntity('carrier', { name });
    });

    document.getElementById('add-door-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const door_name = document.getElementById('door-name').value.trim();
        const direction = document.getElementById('door-dir').value;
        await addEntity('door', { door_name, direction });
    });

    document.getElementById('add-operator-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('op-name').value.trim();
        const initials = document.getElementById('op-initials').value.trim();
        await addEntity('operator', { name, initials });
    });

    // Delete buttons setup
    container.querySelectorAll('.delete-entity-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const entity = btn.getAttribute('data-entity');
            const id = btn.getAttribute('data-id');
            if (confirm(`Are you sure you want to delete this ${entity}?`)) {
                await deleteEntity(entity, id);
            }
        });
    });

    async function addEntity(entity, payload) {
        const res = await fetch(`${CONFIG.apiBase}/admin-entity`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entity, action: 'add', ...payload })
        });
        if (res.ok) {
            await renderAdmin(container);
        } else {
            const err = await res.json();
            alert(`Failed to add: ${err.error || 'Unknown error'}`);
        }
    }

    async function deleteEntity(entity, id) {
        const res = await fetch(`${CONFIG.apiBase}/admin-entity`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entity, action: 'delete', id: parseInt(id) })
        });
        if (res.ok) {
            await renderAdmin(container);
        } else {
            const err = await res.json();
            alert(`Failed to delete: ${err.error || 'Unknown error'}`);
        }
    }
}
// --- PIT APP View --------------------------------------------------------
async function renderPITBoard(container) {
    container.innerHTML = 
        <div class="row align-items-center mb-4">
            <div class="col">
                <span class="text-uppercase text-muted fw-bold" style="font-size: 11px; letter-spacing: 0.05em;">PIT APP</span>
                <h1 class="operations-header-serif">Task Board</h1>
            </div>
            <div class="col-auto">
                <button class="btn btn-outline-primary btn-sm" id="btn-change-operator">
                    <i class="bi bi-person-badge"></i> <span id="current-operator-name">Select Operator</span>
                </button>
            </div>
        </div>

        <div class="row g-4" id="pit-board-content">
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status"></div>
            </div>
        </div>

        <!-- Operator Select Modal -->
        <div class="modal fade" id="operatorModal" tabindex="-1" aria-hidden="true" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered modal-sm">
                <div class="modal-content">
                    <div class="modal-header border-0 pb-0">
                        <h5 class="modal-title fw-bold">Select Operator</h5>
                    </div>
                    <div class="modal-body">
                        <select id="operator-select" class="form-select form-select-lg mb-3">
                            <option value="">-- Choose Operator --</option>
                             + state.metadata.operators.map(o => <option value=" + o.id + "> + o.name + </option>).join('') + 
                        </select>
                        <button class="btn btn-primary w-100 py-2" id="btn-save-operator">Continue</button>
                    </div>
                </div>
            </div>
        </div>
    ;

    const operatorModal = new bootstrap.Modal(document.getElementById('operatorModal'));
    
    // Check local storage for operator
    let operatorId = localStorage.getItem('pit_operator_id');
    let operatorName = localStorage.getItem('pit_operator_name');
    
    if (!operatorId) {
        operatorModal.show();
    } else {
        document.getElementById('current-operator-name').textContent = operatorName;
        loadTasks();
    }
    
    document.getElementById('btn-change-operator').addEventListener('click', () => {
        document.getElementById('operator-select').value = operatorId || '';
        operatorModal.show();
    });
    
    document.getElementById('btn-save-operator').addEventListener('click', () => {
        const sel = document.getElementById('operator-select');
        if (sel.value) {
            operatorId = sel.value;
            operatorName = sel.options[sel.selectedIndex].text;
            localStorage.setItem('pit_operator_id', operatorId);
            localStorage.setItem('pit_operator_name', operatorName);
            document.getElementById('current-operator-name').textContent = operatorName;
            operatorModal.hide();
            loadTasks();
        }
    });

    async function loadTasks() {
        const board = document.getElementById('pit-board-content');
        board.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-primary" role="status"></div></div>';
        
        const res = await fetch(CONFIG.apiBase + '/pit/tasks');
        if (res.ok) {
            const data = await res.json();
            const allTasks = [...data.pit_tasks, ...data.pick_tasks];
            
            // Group tasks
            const ibTasks = allTasks.filter(t => t.task_type === 'IB_Unload');
            const obTasks = allTasks.filter(t => t.task_type === 'OB_Load');
            const pwTasks = allTasks.filter(t => t.task_type === 'Putaway');
            const pickTasks = allTasks.filter(t => t.task_type === 'Pick');
            
            const renderTaskCard = (t) => {
                const isMine = t.operator_name === operatorName;
                const statusBadge = t.status === 'In Progress' ? '<span class="badge bg-warning text-dark">In Progress</span>' : '<span class="badge bg-secondary">Pending</span>';
                const actionBtn = t.status === 'Pending' 
                    ? <button class="btn btn-primary btn-sm w-100 mt-2 btn-start-task" data-id="+t.id+" data-type="+(t.task_type==='Pick'?'Pick':'PIT')+">Start Task</button>
                    : (isMine ? <button class="btn btn-success btn-sm w-100 mt-2 btn-complete-task" data-id="+t.id+" data-type="+(t.task_type==='Pick'?'Pick':'PIT')+">Complete Task</button> : <button class="btn btn-outline-secondary btn-sm w-100 mt-2" disabled>Started by +t.operator_name+</button>);
                
                return 
                    <div class="card mb-2 shadow-sm  + (t.status === 'In Progress' ? (isMine ? 'border-primary' : 'border-warning') : '') + ">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between mb-2">
                                <span class="fw-bold fs-6 mono"> + (t.pick_number || t.bol_shipment_no || 'No Ref') + </span>
                                 + statusBadge + 
                            </div>
                            <div class="text-muted small mb-1"><i class="bi bi-building"></i>  + (t.customer || 'N/A') + </div>
                            <div class="text-muted small mb-2"><i class="bi bi-box"></i>  + (t.product_type || t.product_info || 'N/A') + </div>
                            <div class="d-flex justify-content-between align-items-center mt-3">
                                <span class="badge bg-light text-dark border"> + (t.lane_name || t.from_location || 'Any Lane') + </span>
                            </div>
                             + actionBtn + 
                        </div>
                    </div>
                ;
            };
            
            const renderColumn = (title, tasks, colorClass) => 
                <div class="col-12 col-md-6 col-xl-3">
                    <div class="card bg-light border-0 h-100">
                        <div class="card-header border-0  + colorClass +  text-white py-3 fw-bold d-flex justify-content-between">
                            <span> + title + </span>
                            <span class="badge bg-white text-dark rounded-pill"> + tasks.length + </span>
                        </div>
                        <div class="card-body p-2" style="max-height: 70vh; overflow-y: auto;">
                             + (tasks.length === 0 ? '<div class="text-center text-muted py-4 small">No tasks</div>' : tasks.map(renderTaskCard).join('')) + 
                        </div>
                    </div>
                </div>
            ;
            
            board.innerHTML = 
                renderColumn('Inbound Unload', ibTasks, 'bg-primary') +
                renderColumn('Outbound Load', obTasks, 'bg-info') +
                renderColumn('Putaway', pwTasks, 'bg-secondary') +
                renderColumn('Picking', pickTasks, 'bg-dark');
                
            // Attach events
            document.querySelectorAll('.btn-start-task').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = e.target.getAttribute('data-id');
                    const type = e.target.getAttribute('data-type');
                    await fetch(CONFIG.apiBase + '/pit/tasks/start', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({task_id: id, task_category: type, operator_id: operatorId})
                    });
                    loadTasks();
                });
            });
            document.querySelectorAll('.btn-complete-task').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const id = e.target.getAttribute('data-id');
                    const type = e.target.getAttribute('data-type');
                    await fetch(CONFIG.apiBase + '/pit/tasks/complete', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({task_id: id, task_category: type})
                    });
                    loadTasks();
                });
            });
        }
    }
}
