// Check auth token
if (!localStorage.getItem('token')) {
    window.location.href = '/'; // redirect to main page if not logged in
}

document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.removeItem('token');
    window.location.href = '/';
});

document.getElementById('back-btn').addEventListener('click', () => {
    window.location.href = '/';
});

// Custom Upload Submit
document.getElementById('manual-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('manual-submit-btn');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');
    
    const formData = new FormData();
    formData.append('product_name', document.getElementById('product-name').value);
    formData.append('product_details', document.getElementById('product-details').value);
    formData.append('custom_usp', document.getElementById('custom-usp').value);
    
    const file = document.getElementById('product-image').files[0];
    if(file) formData.append('file', file);
    
    btn.disabled = true; btnText.textContent = 'Analyzing Image & Info...'; spinner.classList.remove('hidden');
    
    const errorMsg = document.getElementById('main-error-msg');
    const resultsDiv = document.getElementById('results');
    errorMsg.textContent = '';
    resultsDiv.classList.add('hidden');

    try {
        const res = await fetch('/api/generate-manual', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('token')
            },
            body: formData
        });

        let data;
        const resClone = res.clone();
        try {
            const text = await res.text();
            data = text ? JSON.parse(text) : {};
        } catch(e) {
            data = await resClone.json();
        }

        if (!res.ok) {
            if(res.status === 401) {
                localStorage.removeItem('token');
                window.location.href = '/';
            }
            throw new Error(data.detail || 'Failed to generate ads');
        }

        renderResults(data);
        resultsDiv.classList.remove('hidden');

    } catch (err) {
        errorMsg.textContent = err.message;
    } finally {
        btn.disabled = false; btnText.textContent = 'Analyze & Generate Ads'; spinner.classList.add('hidden');
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
