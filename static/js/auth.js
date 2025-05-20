/**
 * Authentication helper functions for Tech for Good
 */

// Store user info in localStorage
function setUserSession(userData) {
  console.log('Setting user session:', userData);
  localStorage.setItem('token', userData.access_token);
  localStorage.setItem('userRole', userData.role);
  localStorage.setItem('userId', userData.id);
  localStorage.setItem('userName', userData.name);
  localStorage.setItem('loggedIn', 'true');
}

// Clear user session on logout
function clearUserSession() {
  console.log('Clearing user session');
  localStorage.removeItem('token');
  localStorage.removeItem('userRole');
  localStorage.removeItem('userId');
  localStorage.removeItem('userName');
  localStorage.removeItem('loggedIn');
}

// Check if user is logged in
function isLoggedIn() {
  const loggedIn = localStorage.getItem('loggedIn') === 'true' && localStorage.getItem('token');
  console.log('Checking if user is logged in:', loggedIn);
  return loggedIn;
}

// Get user role
function getUserRole() {
  return localStorage.getItem('userRole');
}

// Redirect to appropriate dashboard based on role
function redirectToDashboard() {
  const role = getUserRole();
  console.log('Redirecting to dashboard for role:', role);
  if (role === 'admin') {
    window.location.href = '/admin/dashboard';
  } else if (role === 'volunteer') {
    window.location.href = '/volunteer/dashboard';
  }
}

// Redirect to login page
function redirectToLogin() {
  console.log('Redirecting to login page');
  window.location.href = '/';
}

// Verify token is valid by calling the backend
async function verifyToken() {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('No token found');
      return false;
    }
    
    console.log('Verifying token with backend');
    const response = await fetch('/auth/user', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('Token verification response status:', response.status);
    
    if (response.ok) {
      console.log('Token is valid');
      const data = await response.json();
      console.log('User data from token validation:', data);
      
      // Update local storage with latest user data if needed
      if (data.user) {
        localStorage.setItem('userName', data.user.name || localStorage.getItem('userName'));
        localStorage.setItem('userRole', data.user.role || localStorage.getItem('userRole'));
        localStorage.setItem('userId', data.user.id || localStorage.getItem('userId'));
      }
      
      return true;
    } else {
      let errorMsg = 'Token is invalid, status: ' + response.status;
      try {
        const errorData = await response.json();
        errorMsg += '\n' + JSON.stringify(errorData);
      } catch (e) {
        // ignore JSON parse error
      }
      alert(errorMsg);
      clearUserSession();
      return false;
    }
  } catch (error) {
    alert('Error verifying token: ' + error);
    return false;
  }
}

// Check authentication and redirect appropriately
async function checkAuthAndRedirect() {
  // Check current page
  const currentPath = window.location.pathname;
  const isMainPage = currentPath === '/';
  const isAdminPage = currentPath.startsWith('/admin/');
  const isVolunteerPage = currentPath.startsWith('/volunteer/');
  
  console.log('Current path:', currentPath);
  
  try {
    // Verify login status
    const tokenValid = await verifyToken();
    const loggedIn = isLoggedIn() && tokenValid;
    
    console.log('Login status:', loggedIn, 'Token valid:', tokenValid);
    
    if (loggedIn) {
      const userRole = getUserRole();
      
      // If on main page and logged in, redirect to appropriate dashboard
      if (isMainPage) {
        console.log('On main page while logged in, redirecting to dashboard');
        redirectToDashboard();
        return;
      }
      
      // If on admin page but not admin, redirect to volunteer dashboard
      if (isAdminPage && userRole !== 'admin') {
        console.log('Non-admin on admin page, redirecting to volunteer dashboard');
        window.location.href = '/volunteer/dashboard';
        return;
      }
      
      console.log('User on appropriate page, no redirect needed');
      // User is on appropriate page, no redirect needed
    } else {
      // If not logged in and on protected page, redirect to login
      if (isAdminPage || isVolunteerPage) {
        console.log('Not logged in on protected page, redirecting to login');
        redirectToLogin();
        return;
      }
    }
  } catch (error) {
    console.error('Error in checkAuthAndRedirect:', error);
    // On error, clear session and redirect to login if on a protected page
    clearUserSession();
    if (isAdminPage || isVolunteerPage) {
      redirectToLogin();
    }
  }
}

// Perform login
async function performLogin(email, password, role) {
  try {
    console.log('Attempting login for:', email, 'with role:', role);
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        password: password,
        role: role
      })
    });

    const data = await response.json();
    console.log('Login response:', data);

    if (response.ok) {
      console.log('Login successful, received data:', data);
      // Store user session data
      setUserSession(data);
      
      // Redirect based on role
      redirectToDashboard();
      return true;
    } else {
      console.error('Login failed:', data.error || 'Unknown error');
      return { error: data.error || 'Login failed' };
    }
  } catch (error) {
    console.error('Login error:', error);
    return { error: 'An error occurred during login' };
  }
}

// Perform logout
function performLogout() {
  clearUserSession();
  redirectToLogin();
} 