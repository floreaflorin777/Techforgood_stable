// Token management - use the functions from auth.js instead
function getToken() {
    return localStorage.getItem('token');
}

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Setup navigation
    setupNavigation();
    
    // Load dashboard data
    loadDashboardData();
    
    // Set up auto-refresh of dashboard data every 5 minutes
    setInterval(loadDashboardData, 300000);
});

function setupNavigation() {
    const links = document.querySelectorAll('.nav-link[data-section]');
    links.forEach(link => {
        link.addEventListener('click', function() {
            // Hide all sections
            document.querySelectorAll('.section').forEach(s => {
                s.classList.add('d-none');
            });
            
            // Show selected section
            const sectionId = this.getAttribute('data-section') + '-section';
            document.getElementById(sectionId).classList.remove('d-none');
            
            // Update active state
            links.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Load data for the section
            if (this.getAttribute('data-section') === 'volunteers') {
                loadVolunteers();
            } else if (this.getAttribute('data-section') === 'inventory') {
                loadInventory();
            } else if (this.getAttribute('data-section') === 'shifts') {
                loadShifts();
            } else if (this.getAttribute('data-section') === 'analytics') {
                loadAnalytics();
            }
        });
    });
}

// Load dashboard data
async function loadDashboardData() {
    try {
        const token = getToken();
        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };

        // Load statistics
        const statsResponse = await fetch('/api/admin/stats', { headers });
        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            document.getElementById('total-volunteers').textContent = stats.totalVolunteers || 0;
            document.getElementById('active-volunteers').textContent = stats.activeVolunteers || 0;
            document.getElementById('total-items').textContent = stats.totalItems || 0;
            document.getElementById('low-stock').textContent = stats.lowStockItems || 0;
        }

        // Load recent shifts
        const shiftsResponse = await fetch('/api/admin/recent-shifts', { headers });
        if (shiftsResponse.ok) {
            const shifts = await shiftsResponse.json();
            const shiftsTable = document.getElementById('recent-shifts').querySelector('tbody');
            shiftsTable.innerHTML = '';
            
            shifts.forEach(shift => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${shift.volunteerName}</td>
                    <td>${new Date(shift.startTime).toLocaleDateString()}</td>
                    <td><span class="badge bg-${getStatusColor(shift.status)}">${shift.status}</span></td>
                `;
                shiftsTable.appendChild(row);
            });
        }

        // Load low stock items
        const lowStockResponse = await fetch('/api/admin/low-stock', { headers });
        if (lowStockResponse.ok) {
            const items = await lowStockResponse.json();
            const itemsTable = document.getElementById('low-stock-items').querySelector('tbody');
            itemsTable.innerHTML = '';
            
            items.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.name}</td>
                    <td>${item.quantity} ${item.unit}</td>
                    <td><span class="badge bg-warning">Low Stock</span></td>
                `;
                itemsTable.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Load volunteers data
async function loadVolunteers() {
    try {
        const token = getToken();
        const response = await fetch('/api/admin/volunteers', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const volunteers = await response.json();
            const table = document.getElementById('volunteers-table').querySelector('tbody');
            table.innerHTML = '';
            
            volunteers.forEach(volunteer => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${volunteer.name}</td>
                    <td>${volunteer.email}</td>
                    <td>${volunteer.phone || 'N/A'}</td>
                    <td><span class="badge bg-${volunteer.isActive ? 'success' : 'secondary'}">${volunteer.isActive ? 'Active' : 'Inactive'}</span></td>
                    <td>
                        <button class="btn btn-sm btn-warning edit-volunteer" data-id="${volunteer.id}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger delete-volunteer" data-id="${volunteer.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                table.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading volunteers:', error);
    }
}

// Load inventory data
async function loadInventory() {
    try {
        const token = getToken();
        const response = await fetch('/api/admin/inventory', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const items = await response.json();
            const table = document.getElementById('inventory-table').querySelector('tbody');
            table.innerHTML = '';
            
            items.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.name}</td>
                    <td>${item.quantity}</td>
                    <td>${item.unit || 'N/A'}</td>
                    <td>${item.category || 'N/A'}</td>
                    <td>${item.expiryDate ? new Date(item.expiryDate).toLocaleDateString() : 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-warning edit-item" data-id="${item.id}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger delete-item" data-id="${item.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                table.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

// Load shifts data
async function loadShifts() {
    try {
        const token = getToken();
        const response = await fetch('/api/admin/shifts', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const shifts = await response.json();
            const table = document.getElementById('shifts-table').querySelector('tbody');
            table.innerHTML = '';
            
            shifts.forEach(shift => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${shift.volunteerName}</td>
                    <td>${formatDateTime(shift.startTime)}</td>
                    <td>${formatDateTime(shift.endTime)}</td>
                    <td><span class="badge bg-${getStatusColor(shift.status)}">${shift.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-warning edit-shift" data-id="${shift.id}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger delete-shift" data-id="${shift.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                table.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Error loading shifts:', error);
    }
}

// Load analytics data
async function loadAnalytics() {
    try {
        // This function would typically fetch analytics data 
        // and update charts. For now, it's a placeholder.
        console.log('Loading analytics data...');
        
        // You can use Chart.js to create charts here
        // Example:
        // const volunteerCtx = document.getElementById('volunteerChart').getContext('2d');
        // const volunteerChart = new Chart(volunteerCtx, { ... });
        
        // const inventoryCtx = document.getElementById('inventoryChart').getContext('2d');
        // const inventoryChart = new Chart(inventoryCtx, { ... });
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// Helper functions
function getStatusColor(status) {
    switch(status.toLowerCase()) {
        case 'pending': return 'warning';
        case 'confirmed': return 'success';
        case 'cancelled': return 'danger';
        case 'completed': return 'info';
        default: return 'secondary';
    }
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
} 