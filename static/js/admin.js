// Function to fetch and update statistics
async function updateStatistics() {
    try {
        // Fetch volunteer statistics
        const volunteerResponse = await fetch('/api/analytics/volunteers', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const volunteerData = await volunteerResponse.json();
        
        // Update volunteer statistics
        document.getElementById('total-volunteers').textContent = volunteerData.total_volunteers || 0;
        document.getElementById('active-volunteers').textContent = volunteerData.active_volunteers || 0;

        // Fetch inventory statistics
        const inventoryResponse = await fetch('/api/analytics/inventory', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const inventoryData = await inventoryResponse.json();
        
        // Update inventory statistics
        document.getElementById('total-items').textContent = inventoryData.total_items || 0;
        document.getElementById('low-stock').textContent = inventoryData.low_stock_items || 0;

        // Update low stock alerts table
        const lowStockTable = document.getElementById('low-stock-items').getElementsByTagName('tbody')[0];
        lowStockTable.innerHTML = '';
        inventoryData.low_stock_items_list.forEach(item => {
            const row = lowStockTable.insertRow();
            row.insertCell(0).textContent = item.name;
            row.insertCell(1).textContent = `${item.quantity} ${item.unit}`;
            row.insertCell(2).textContent = item.quantity <= item.min_quantity ? 'Critical' : 'Low';
        });

        // Fetch recent shifts
        const shiftsResponse = await fetch('/api/shifts/recent', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const shiftsData = await shiftsResponse.json();
        
        // Update recent shifts table
        const shiftsTable = document.getElementById('recent-shifts').getElementsByTagName('tbody')[0];
        shiftsTable.innerHTML = '';
        shiftsData.shifts.forEach(shift => {
            const row = shiftsTable.insertRow();
            row.insertCell(0).textContent = shift.volunteer_name;
            row.insertCell(1).textContent = new Date(shift.start_time).toLocaleDateString();
            row.insertCell(2).textContent = shift.status;
        });

    } catch (error) {
        console.error('Error fetching statistics:', error);
        // Show error message to user
        alert('Error loading dashboard data. Please try again later.');
    }
}

// Update statistics when page loads
document.addEventListener('DOMContentLoaded', () => {
    updateStatistics();
    // Update statistics every 5 minutes
    setInterval(updateStatistics, 300000);
});

// Handle navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const section = e.target.closest('.nav-link').dataset.section;
        
        // Hide all sections
        document.querySelectorAll('.section').forEach(s => s.classList.add('d-none'));
        
        // Show selected section
        document.getElementById(`${section}-section`).classList.remove('d-none');
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        e.target.closest('.nav-link').classList.add('active');
    });
});

// Handle logout
document.getElementById('logout').addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('token');
    window.location.href = '/login';
}); 