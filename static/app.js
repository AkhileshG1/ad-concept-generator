let isLogin = true;

const authOverlay = document.getElementById('auth-overlay');
const loginNavBtn = document.getElementById('login-nav-btn');
const dashboardNavBtn = document.getElementById('dashboard-nav-btn');
const logoutBtn = document.getElementById('logout-btn');
const closeAuthBtn = document.getElementById('close-auth-btn');

const toggleBtn = document.getElementById('toggle-auth');
const authTitle = document.getElementById('auth-title');
const authBtnText = document.querySelector('#auth-btn .btn-text');

// Initialize state on load
function updateAuthState() {
    const hasToken = !!localStorage.getItem('token');
    if (hasToken) {
        loginNavBtn.classList.add('hidden');
        dashboardNavBtn.classList.remove('hidden');
        logoutBtn.classList.remove('hidden');
    } else {
        loginNavBtn.classList.remove('hidden');
        dashboardNavBtn.classList.add('hidden');
        logoutBtn.classList.add('hidden');
    }
}
updateAuthState();

loginNavBtn.addEventListener('click', () => {
    authOverlay.classList.remove('hidden');
});

dashboardNavBtn.addEventListener('click', () => {
    window.location.href = '/dashboard.html';
});

closeAuthBtn.addEventListener('click', () => {
    authOverlay.classList.add('hidden');
});

logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('token');
    updateAuthState();
});

toggleBtn.addEventListener('click', () => {
    isLogin = !isLogin;
    authTitle.textContent = isLogin ? 'Welcome Back' : 'Create Account';
    authBtnText.textContent = isLogin ? 'Login' : 'Sign Up';
    toggleBtn.textContent = isLogin ? 'Sign up' : 'Login';
    document.querySelector('.auth-toggle').childNodes[0].textContent = isLogin ? "Don't have an account? " : "Already have an account? ";
});

document.getElementById('auth-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('auth-username').value;
    const password = document.getElementById('auth-password').value;
    const btn = document.getElementById('auth-btn');
    const spinner = btn.querySelector('.spinner');
    const err = document.getElementById('auth-error');
    
    err.textContent = "";
    btn.disabled = true; spinner.classList.remove('hidden'); authBtnText.classList.add('hidden');

    try {
        if(isLogin) {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail || 'Login failed');
            
            localStorage.setItem('token', data.access_token);
            authOverlay.classList.add('hidden');
            updateAuthState();
            
            // Redirect straight to dashboard on login
            window.location.href = '/dashboard.html';
            
        } else {
            const res = await fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({username, password})
            });
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail || 'Signup failed');
            
            // Switch to login automatically
            isLogin = true;
            authTitle.textContent = 'Welcome Back';
            authBtnText.textContent = 'Login';
            toggleBtn.textContent = 'Sign up';
            err.textContent = "Account created. You can now login.";
            err.style.color = "#10b981";
            setTimeout(() => err.style.color = "", 3000);
        }
    } catch (error) {
        err.textContent = error.message;
    } finally {
        btn.disabled = false; spinner.classList.add('hidden'); authBtnText.classList.remove('hidden');
    }
});

// Generic Fetch Logic
async function callGenerate(url, opts) {
    const errorMsg = document.getElementById('main-error-msg');
    const resultsDiv = document.getElementById('results');
    errorMsg.textContent = '';
    resultsDiv.classList.add('hidden');
    
    opts.headers = opts.headers || {};
    const token = localStorage.getItem('token');
    if (token) {
        opts.headers['Authorization'] = 'Bearer ' + token;
    }
    
    const res = await fetch(url, opts);
    let data;
    try {
        if(res.ok) {
            const jsonText = await res.json();
            data = typeof jsonText === 'string' ? JSON.parse(jsonText) : jsonText;
        } else {
            data = await res.json();
        }
    } catch(e) {
        throw new Error('Failed to parse backend response');
    }

    if (!res.ok) {
        throw new Error(data.detail || 'Failed to generate ads');
    }

    renderResults(data);
    resultsDiv.classList.remove('hidden');
}

// Scrape Submit
document.getElementById('url-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('url-submit-btn');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');
    
    btn.disabled = true; btnText.textContent = 'Analyzing...'; spinner.classList.remove('hidden');
    try {
        await callGenerate('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: document.getElementById('url-input').value })
        });
    } catch (err) {
        document.getElementById('main-error-msg').textContent = err.message;
    } finally {
        btn.disabled = false; btnText.textContent = 'Generate Ads'; spinner.classList.add('hidden');
    }
});

function renderResults(data) {
    document.getElementById('usp-text').textContent = data.usp || "No USP found.";
    
    const rsaContainer = document.getElementById('rsa-container');
    rsaContainer.innerHTML = ''; 
    if (data.rsas && data.rsas.length > 0) {
        data.rsas.forEach((rsa, index) => {
            const card = document.createElement('div'); card.className = 'card rsa-item';
            const hl = rsa.headlines.map(h => `<p><strong>HL:</strong> ${h}</p>`).join('');
            const desc = rsa.descriptions.map(d => `<p><strong>Desc:</strong> ${d}</p>`).join('');
            card.innerHTML = `<h3>Concept ${index + 1}</h3><div style="margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">${hl}</div><div>${desc}</div>`;
            rsaContainer.appendChild(card);
        });
    }
    
    const displayContainer = document.getElementById('display-container');
    displayContainer.innerHTML = ''; 
    if (data.displayAds && data.displayAds.length > 0) {
        data.displayAds.forEach((ad, index) => {
            const card = document.createElement('div'); card.className = 'card display-item';
            card.innerHTML = `<h3>Display Ad ${index + 1}</h3><p style="margin-bottom: 1rem;"><strong>Visual:</strong> ${ad.concept}</p><p style="margin-bottom: 0.5rem;"><strong>Headline:</strong> <span style="color:#60a5fa">${ad.headline}</span></p><p><strong>Copy:</strong> ${ad.copy}</p>`;
            displayContainer.appendChild(card);
        });
    }
}
