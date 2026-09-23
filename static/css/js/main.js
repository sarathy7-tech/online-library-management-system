/* ==================== TOAST NOTIFICATIONS ==================== */
function showToast(message, type = 'success') {
    // Remove old toast if exists
    const oldToast = document.querySelector('.custom-toast');
    if (oldToast) oldToast.remove();

    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    // Show animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto hide after 3.5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

/* ==================== FORM VALIDATION ==================== */
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

    // Remove old error messages
    form.querySelectorAll('.error-message').forEach(el => el.remove());
    form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

    inputs.forEach(input => {
        const value = input.value.trim();

        if (!value) {
            showError(input, 'This field is required');
            isValid = false;
            return;
        }

        // Email validation
        if (input.type === 'email') {
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(value)) {
                showError(input, 'Please enter a valid email');
                isValid = false;
            }
        }

        // Password minimum length
        if (input.type === 'password' && value.length < 6) {
            showError(input, 'Password must be at least 6 characters');
            isValid = false;
        }

        // Phone validation (optional basic)
        if (input.name === 'phone' && value && value.length < 10) {
            showError(input, 'Please enter a valid phone number');
            isValid = false;
        }
    });

    // Password confirmation check
    const password1 = form.querySelector('input[name="password1"]');
    const password2 = form.querySelector('input[name="password2"]');
    if (password1 && password2 && password1.value !== password2.value) {
        showError(password2, 'Passwords do not match');
        isValid = false;
    }

    return isValid;
}

function showError(input, message) {
    input.classList.add('is-invalid');

    const error = document.createElement('div');
    error.className = 'error-message text-danger small mt-1';
    error.innerText = message;
    input.parentNode.appendChild(error);
}

/* ==================== AUTO APPLY ON PAGE LOAD ==================== */
document.addEventListener('DOMContentLoaded', function() {

    // Apply validation to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault(); // Stop form submit if invalid
                showToast('Please fix the errors in the form', 'error');
            }
        });
    });

    // Convert Django messages into toasts (if any)
    const djangoMessages = document.querySelectorAll('.alert');
    djangoMessages.forEach(msg => {
        let type = 'success';
        if (msg.classList.contains('alert-error') || msg.classList.contains('alert-danger')) {
            type = 'error';
        } else if (msg.classList.contains('alert-warning')) {
            type = 'warning';
        }
        showToast(msg.innerText.trim(), type);
        msg.style.display = 'none'; // Hide original alert
    });
});