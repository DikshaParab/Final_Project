document.addEventListener('DOMContentLoaded', function() {
    // Handle leave form submission
    const leaveForm = document.getElementById('leaveForm');
    if (leaveForm) {
        leaveForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate dates
            const startDate = new Date(document.getElementById('start_date').value);
            const endDate = new Date(document.getElementById('end_date').value);
            
            if (startDate > endDate) {
                alert('End date must be after start date');
                return;
            }
            
            // Submit form
            fetch(leaveForm.action, {
                method: 'POST',
                body: new FormData(leaveForm)
            })
            .then(response => {
                if (response.redirected) {
                    // Show success modal
                    const successModal = document.getElementById('successModal');
                    successModal.style.display = 'flex';
                    
                    // Close modal and redirect
                    const okBtn = document.getElementById('okBtn');
                    okBtn.addEventListener('click', function() {
                        window.location.href = response.url;
                    });
                    
                    // Close button
                    const closeBtn = successModal.querySelector('.close');
                    closeBtn.addEventListener('click', function() {
                        successModal.style.display = 'none';
                        window.location.href = response.url;
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while submitting your leave application');
            });
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