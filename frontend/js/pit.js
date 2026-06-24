const API_BASE = '/api';

// Fetch Active Trucks
async function fetchActiveTrucks() {
    try {
        const response = await fetch(`${API_BASE}/pit/tasks`);
        if (!response.ok) throw new Error('Failed to fetch trucks');
        
        const data = await response.json();
        renderTrucks(data.trucks);
    } catch (err) {
        document.getElementById('errorAlert').textContent = err.message;
        document.getElementById('errorAlert').classList.remove('d-none');
    } finally {
        document.getElementById('loadingIndicator').classList.add('d-none');
    }
}

// Render Truck Cards
function renderTrucks(trucks) {
    const container = document.getElementById('truckCardsContainer');
    container.innerHTML = '';

    if (!trucks || trucks.length === 0) {
        container.innerHTML = `<div class="col-12 text-center text-muted py-5"><h4>No checked-in trucks at the moment</h4></div>`;
        return;
    }

    trucks.forEach(truck => {
        // Status Badge Color
        let badgeClass = 'bg-secondary';
        if (truck.pit_status === 'Pending') badgeClass = 'bg-warning text-dark';
        if (truck.pit_status === 'In Progress') badgeClass = 'bg-primary';

        const col = document.createElement('div');
        col.className = 'col-12 col-md-6 col-xl-4';
        
        let actionArea = '';
        if (truck.pit_status === 'Pending') {
            actionArea = `
                <div class="mt-3">
                    <label class="form-label small text-muted text-uppercase fw-bold">Operator Name</label>
                    <div class="input-group">
                        <input type="text" class="form-control bg-dark border-secondary text-light" id="op-name-${truck.appt_id}" placeholder="Type your name...">
                        <button class="btn btn-success" onclick="startTask(${truck.appt_id})">Start Task</button>
                    </div>
                </div>
            `;
        } else if (truck.pit_status === 'In Progress') {
            actionArea = `
                <div class="mt-3 p-3 bg-dark border border-secondary rounded">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted text-uppercase d-block mb-1">Assigned To</small>
                            <strong>${truck.operator_name || 'Unknown'}</strong>
                        </div>
                        <button class="btn btn-primary" onclick="completeTask(${truck.appt_id})">Complete</button>
                    </div>
                </div>
            `;
        }

        col.innerHTML = `
            <div class="card h-100 bg-black border-secondary truck-card shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h4 class="card-title font-serif mb-0">${truck.trailer_no || 'Unknown Trailer'}</h4>
                        <span class="badge ${badgeClass} status-badge">${truck.pit_status}</span>
                    </div>
                    
                    <div class="row g-2 small text-muted mb-3">
                        <div class="col-6">
                            <span class="d-block text-uppercase" style="font-size:0.7em; letter-spacing:1px;">BOL / Shipment</span>
                            <span class="text-light fw-medium">${truck.bol_shipment_no || 'N/A'}</span>
                        </div>
                        <div class="col-6">
                            <span class="d-block text-uppercase" style="font-size:0.7em; letter-spacing:1px;">Type</span>
                            <span class="text-light fw-medium">${truck.appt_type || 'N/A'}</span>
                        </div>
                        <div class="col-6">
                            <span class="d-block text-uppercase" style="font-size:0.7em; letter-spacing:1px;">Door</span>
                            <span class="text-light fw-medium">${truck.door_name || 'Unassigned'}</span>
                        </div>
                        <div class="col-6">
                            <span class="d-block text-uppercase" style="font-size:0.7em; letter-spacing:1px;">Wait Time</span>
                            <span class="text-light fw-medium">${Math.floor(truck.wait_minutes || 0)} mins</span>
                        </div>
                    </div>

                    ${actionArea}
                </div>
            </div>
        `;
        container.appendChild(col);
    });
}

// Start Task
async function startTask(apptId) {
    const nameInput = document.getElementById(`op-name-${apptId}`);
    const operatorName = nameInput.value.trim();
    
    if (!operatorName) {
        alert("Please enter your name to start the task.");
        nameInput.focus();
        return;
    }

    // Save name to localStorage for future convenience
    localStorage.setItem('pit_last_operator', operatorName);

    try {
        const response = await fetch(`${API_BASE}/pit/tasks/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ appt_id: apptId, operator_name: operatorName })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to start task');
        }
        
        fetchActiveTrucks();
    } catch (err) {
        alert(err.message);
    }
}

// Complete Task
async function completeTask(apptId) {
    if (!confirm("Are you sure this task is complete?")) return;
    
    try {
        const response = await fetch(`${API_BASE}/pit/tasks/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ appt_id: apptId })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to complete task');
        }
        
        fetchActiveTrucks();
    } catch (err) {
        alert(err.message);
    }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    fetchActiveTrucks();
    // Refresh every 15 seconds automatically
    setInterval(fetchActiveTrucks, 15000);
});

// Auto-fill operator name if known
document.addEventListener('focusin', (e) => {
    if(e.target && e.target.id && e.target.id.startsWith('op-name-')) {
        const savedName = localStorage.getItem('pit_last_operator');
        if(savedName && !e.target.value) {
            e.target.value = savedName;
            e.target.select();
        }
    }
});
