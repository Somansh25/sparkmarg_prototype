/* =====================================================================
   SparkMarg Authentication Engine
   ===================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const authController = {
    /**
     * Bind form observers for both login and registration pipelines
     */
    init() {
      const loginForm = document.getElementById('login-form');
      const registerForm = document.getElementById('register-form');

      if (loginForm) {
        loginForm.addEventListener('submit', (e) => this.handleLogin(e));
      }
      if (registerForm) {
        registerForm.addEventListener('submit', (e) => this.handleRegistration(e));
      }
    },

    /**
     * Process authentication verification requests
     */
    async handleLogin(e) {
      e.preventDefault();
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      const submitBtn = document.getElementById('submit-btn');

      this.setLoadingState(submitBtn, true);

      try {
        const response = await window.SparkMarg.apiRequest('/api/auth/login', {
          method: 'POST',
          body: { email, password }
        });

        if (response && response.access_token) {
          localStorage.setItem('access_token', response.access_token);
        }
        
        window.SparkMarg.showAlert('Authentication successful! Diverting to workspace...', 'success');
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 1200);

      } catch (error) {
        window.SparkMarg.showAlert(error.message || 'Invalid credentials provided.', 'danger');
        this.setLoadingState(submitBtn, false);
      }
    },

    /**
     * Process new engineer profile generation entries
     */
    async handleRegistration(e) {
      e.preventDefault();
      const username = document.getElementById('username').value;
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      const submitBtn = document.getElementById('submit-btn');

      this.setLoadingState(submitBtn, true);

      try {
        await window.SparkMarg.apiRequest('/api/auth/register', {
          method: 'POST',
          body: { username, email, password }
        });

        window.SparkMarg.showAlert('Account provisioned successfully! Opening portal...', 'success');
        setTimeout(() => {
          window.location.href = '/login';
        }, 1200);

      } catch (error) {
        window.SparkMarg.showAlert(error.message || 'Registration failed. Identity may already exist.', 'danger');
        this.setLoadingState(submitBtn, false);
      }
    },

    /**
     * Toggle button interaction blocks during async request operations
     */
    setLoadingState(buttonElement, isLoading) {
      if (!buttonElement) return;
      if (isLoading) {
        buttonElement.disabled = true;
        buttonElement.textContent = 'Processing...';
      } else {
        buttonElement.disabled = false;
        buttonElement.textContent = buttonElement.id === 'submit-btn' ? 'Access Engine' : 'Create Account';
      }
    }
  };

  authController.init();
});