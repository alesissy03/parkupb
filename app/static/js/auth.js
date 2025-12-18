/**
 * Script pentru gestionarea autentificarii (login si register)
 */

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginSubmit);
    }

    const registerForm = document.querySelector('form[action="/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegisterSubmit);
    }

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
});

async function handleLoginSubmit(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorContainer = document.getElementById('login-errors');
    
    errorContainer.innerHTML = '';
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        const responseText = await response.text();
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error('Răspuns INVALID:');
            console.error('Status:', response.status);
            console.error('Content-Type:', response.headers.get('Content-Type'));
            console.error('Body (primele 1000 caractere):', responseText.substring(0, 1000));
            showError(errorContainer, 'Eroare server: răspuns invalid.');
            return;
        }
        
        if (response.ok) {
            console.log('Login reușit:', data);
            window.location.href = '/';
        } else {
            showError(errorContainer, data.message || 'Eroare la login');
        }
    } catch (error) {
        console.error('Eroare de conexiune:', error);
        showError(errorContainer, 'Eroare de conexiune: ' + error.message);
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    
    const fullName = document.getElementById('full_name').value;
    const email = document.getElementById('email').value;
    const role = document.getElementById('role').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const errorContainer = document.getElementById('register-errors');
    
    errorContainer.innerHTML = '';
    
    if (password !== confirmPassword) {
        showError(errorContainer, 'Parolele nu se potrivesc!');
        return;
    }
    
    if (password.length < 8) {
        showError(errorContainer, 'Parola trebuie să aibă cel puțin 8 caractere!');
        return;
    }
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                full_name: fullName,
                email: email,
                role: role,
                password: password
            })
        });
        
        const responseText = await response.text();
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error('Răspuns INVALID:');
            console.error('Status:', response.status);
            console.error('Content-Type:', response.headers.get('Content-Type'));
            console.error('Body (primele 1000 caractere):', responseText.substring(0, 1000));
            showError(errorContainer, 'Eroare server: răspuns invalid. Deschide F12 → Console pentru detalii!');
            return;
        }
        
        if (response.ok) {
            console.log('Înregistrare reușită:', data);
            alert('Cont creat cu succes! Te poți autentifica acum.');
            window.location.href = '/login';
        } else {
            showError(errorContainer, data.message || 'Eroare la înregistrare');
        }
    } catch (error) {
        console.error('Eroare de conexiune:', error);
        showError(errorContainer, 'Eroare de conexiune: ' + error.message);
    }
}

async function handleLogout(event) {
    event.preventDefault();
    
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('Logout reușit');
            window.location.href = '/';
        } else {
            console.error('Eroare la logout:', data.message);
            alert('Eroare la logout: ' + data.message);
        }
    } catch (error) {
        console.error('Eroare de conexiune:', error);
        alert('Eroare de conexiune la logout');
    }
}

function showError(container, message) {
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            ${message}
        </div>
    `;
}
