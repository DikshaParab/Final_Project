document.addEventListener('DOMContentLoaded', function() {
    // Initialize calendar
    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: [
                {
                    title: 'Company Holiday',
                    start: '2023-07-04',
                    allDay: true,
                    color: '#e74c3c'
                },
                {
                    title: 'Team Meeting',
                    start: '2023-07-12T10:00:00',
                    end: '2023-07-12T11:30:00',
                    color: '#3498db'
                }
            ]
        });
        calendar.render();
    }
    
    // Handle leave approval modal
    const approvalModal = document.getElementById('approvalModal');
    const approveBtns = document.querySelectorAll('.table .btn-primary');
    const rejectBtns = document.querySelectorAll('.table .btn-danger');
    
    if (approvalModal) {
        const closeBtn = approvalModal.querySelector('.close');
        const cancelBtn = document.getElementById('cancelBtn');
        
        // Open modal for approval
        approveBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const row = this.closest('tr');
                document.getElementById('modalEmployeeName').textContent = row.cells[0].textContent;
                document.getElementById('modalLeavePeriod').textContent = row.cells[1].textContent;
                document.getElementById('modalLeaveReason').textContent = row.cells[2].textContent;
                document.getElementById('modalLeaveStatus').textContent = 'Pending';
                
                approvalModal.style.display = 'flex';
                
                // Set up approve button
                document.getElementById('approveBtn').onclick = function() {
                    // In a real app, you would send an API request here
                    alert('Leave approved!');
                    approvalModal.style.display = 'none';
                    row.remove();
                };
            });
        });
        
        // Open modal for rejection
        rejectBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const row = this.closest('tr');
                document.getElementById('modalEmployeeName').textContent = row.cells[0].textContent;
                document.getElementById('modalLeavePeriod').textContent = row.cells[1].textContent;
                document.getElementById('modalLeaveReason').textContent = row.cells[2].textContent;
                document.getElementById('modalLeaveStatus').textContent = 'Pending';
                
                approvalModal.style.display = 'flex';
                
                // Set up reject button
                document.getElementById('rejectBtn').onclick = function() {
                    // In a real app, you would send an API request here
                    alert('Leave rejected!');
                    approvalModal.style.display = 'none';
                    row.remove();
                };
            });
        });
        
        // Close modal
        closeBtn.addEventListener('click', function() {
            approvalModal.style.display = 'none';
        });
        
        cancelBtn.addEventListener('click', function() {
            approvalModal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
});