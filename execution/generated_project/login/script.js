document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const messageDisplay = document.getElementById('message');

    loginForm.addEventListener('submit', (event) => {
        event.preventDefault(); // Prevent default form submission

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        // Basic validation
        if (username === '' || password === '') {
            messageDisplay.textContent = 'Please enter both username and password.';
            messageDisplay.style.color = 'red';
            return;
        }

        // Simple login logic (for demonstration purposes)
        if (username === 'user' && password === 'password') {
            messageDisplay.textContent = 'Login successful!';
            messageDisplay.style.color = 'green';
            // In a real application, you would redirect to another page or set a session/token
            // window.location.href = '/dashboard';
        } else {
            messageDisplay.textContent = 'Invalid username or password.';
            messageDisplay.style.color = 'red';
        }
    });
});