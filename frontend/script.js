const DJANGO_URL = 'http://127.0.0.1:8000/api';
const FASTAPI_URL = 'http://127.0.0.1:8001/api';

let jwtToken = localStorage.getItem('token') || '';
let currentUser = localStorage.getItem('username') || '';

function updateAuthUI() {
    const greeting = document.getElementById('userGreeting');
    const logoutBtn = document.getElementById('logoutBtn');
    const authSec = document.getElementById('authSection');
    const appSec = document.getElementById('appSection');

    if (jwtToken) {
        greeting.textContent = `Logged in as: ${currentUser}`;
        logoutBtn.style.display = 'inline-block';
        authSec.style.display = 'none';
        appSec.style.display = 'block';
        loadCards();
        loadTransactions();
    } else {
        greeting.textContent = 'Not Logged In';
        logoutBtn.style.display = 'none';
        authSec.style.display = 'grid';
        appSec.style.display = 'none';
    }
}

function showBox(elementId, msg, isError = false) {
    const el = document.getElementById(elementId);
    el.className = 'output ' + (isError ? 'error' : 'success');
    el.textContent = typeof msg === 'object' ? JSON.stringify(msg) : msg;
}

// 1. REGISTRATION
document.getElementById('regForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const res = await fetch(`${DJANGO_URL}/auth/register/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: document.getElementById('regUser').value,
                email: document.getElementById('regEmail').value,
                password: document.getElementById('regPass').value,
            })
        });
        const data = await res.json();
        if (res.ok) {
            jwtToken = data.token;
            currentUser = data.username;
            localStorage.setItem('token', jwtToken);
            localStorage.setItem('username', currentUser);
            updateAuthUI();
        } else {
            showBox('regOutput', data, true);
        }
    } catch (err) {
        showBox('regOutput', err.message, true);
    }
});

// 2. LOGIN (JWT)
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const res = await fetch(`${DJANGO_URL}/auth/login/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: document.getElementById('loginUser').value,
                password: document.getElementById('loginPass').value,
            })
        });
        const data = await res.json();
        if (res.ok) {
            jwtToken = data.token;
            currentUser = data.username;
            localStorage.setItem('token', jwtToken);
            localStorage.setItem('username', currentUser);
            updateAuthUI();
        } else {
            showBox('loginOutput', data.error || 'Login failed', true);
        }
    } catch (err) {
        showBox('loginOutput', err.message, true);
    }
});

// 3. LOGOUT
document.getElementById('logoutBtn').addEventListener('click', () => {
    jwtToken = '';
    currentUser = '';
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    updateAuthUI();
});

// 4. ADD CARD
document.getElementById('addCardForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const res = await fetch(`${DJANGO_URL}/cards/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({
                cardholder_name: document.getElementById('cName').value,
                card_number: document.getElementById('cNumber').value,
                expiration_month: parseInt(document.getElementById('cExpM').value),
                expiration_year: parseInt(document.getElementById('cExpY').value),
                cvv: document.getElementById('cCVV').value,
                credit_limit: parseFloat(document.getElementById('cLimit').value)
            })
        });
        const data = await res.json();
        if (res.ok) {
            showBox('addCardOutput', 'Card registered securely.');
            loadCards();
            document.getElementById('addCardForm').reset();
        } else {
            showBox('addCardOutput', data, true);
        }
    } catch (err) {
        showBox('addCardOutput', err.message, true);
    }
});

// 5. VIEW SAVED CARDS
async function loadCards() {
    try {
        const res = await fetch(`${DJANGO_URL}/cards/`, {
            headers: {'Authorization': `Bearer ${jwtToken}`}
        });
        const cards = await res.json();
        const container = document.getElementById('cardsList');
        if (!cards.length) {
            container.innerHTML = '<p style="padding:10px;">No saved cards found.</p>';
            return;
        }

        let html = `<table>
            <tr><th>Holder</th><th>Masked Card</th><th>Expiry</th><th>Available Balance</th><th>Action</th></tr>`;
        cards.forEach(c => {
            html += `<tr>
                <td>${c.cardholder_name}</td>
                <td><strong>${c.masked_card}</strong></td>
                <td>${c.expiration_month}/${c.expiration_year}</td>
                <td>$${parseFloat(c.available_balance).toFixed(2)}</td>
                <td><button class="btn-danger" onclick="deleteCard(${c.id})">Delete</button></td>
            </tr>`;
        });
        html += `</table>`;
        container.innerHTML = html;
    } catch (err) {
        console.error(err);
    }
}

// 6. DELETE CARD
window.deleteCard = async function(cardId) {
    if (!confirm('Are you sure you want to delete this card?')) return;
    try {
        const res = await fetch(`${DJANGO_URL}/cards/${cardId}/`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${jwtToken}`}
        });
        if (res.ok) {
            loadCards();
        } else {
            alert('Could not delete card.');
        }
    } catch (err) {
        alert(err.message);
    }
};

// 7. MAKE PAYMENT (FASTAPI)
document.getElementById('paymentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const res = await fetch(`${FASTAPI_URL}/payments/pay`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({
                cardholder_name: document.getElementById('pName').value,
                card_number: document.getElementById('pNumber').value,
                expiration_month: parseInt(document.getElementById('pExpM').value),
                expiration_year: parseInt(document.getElementById('pExpY').value),
                cvv: document.getElementById('pCVV').value,
                amount: parseFloat(document.getElementById('pAmount').value),
                merchant: document.getElementById('pMerchant').value
            })
        });
        const data = await res.json();
        if (data.status === "SUCCESS") {
            showBox('paymentOutput', `Success! Ref: ${data.reference_id}, New Balance: $${data.remaining_balance}`);
        } else {
            showBox('paymentOutput', `${data.status}: ${data.reason || data.message || 'Payment Declined'}`, true);
        }
        loadCards();
        loadTransactions();
    } catch (err) {
        showBox('paymentOutput', err.message, true);
    }
});

// 8. VIEW TRANSACTIONS (DJANGO)
async function loadTransactions() {
    try {
        const res = await fetch(`${DJANGO_URL}/transactions/`, {
            headers: {'Authorization': `Bearer ${jwtToken}`}
        });
        const txns = await res.json();
        const container = document.getElementById('txnList');
        if (!txns.length) {
            container.innerHTML = '<p style="padding:10px;">No transactions recorded.</p>';
            return;
        }

        let html = `<table>
            <tr><th>Reference ID</th><th>Card</th><th>Merchant</th><th>Amount</th><th>Status</th><th>Message</th><th>Timestamp</th></tr>`;
        txns.forEach(t => {
            html += `<tr>
                <td><code>${t.reference_id}</code></td>
                <td>${t.card_display || 'N/A'}</td>
                <td>${t.merchant}</td>
                <td>$${parseFloat(t.amount).toFixed(2)}</td>
                <td><span class="status-${t.status}">${t.status}</span></td>
                <td>${t.message || '-'}</td>
                <td>${new Date(t.timestamp).toLocaleString()}</td>
            </tr>`;
        });
        html += `</table>`;
        container.innerHTML = html;
    } catch (err) {
        console.error(err);
    }
}

document.getElementById('refreshCardsBtn').addEventListener('click', loadCards);
document.getElementById('refreshTxnBtn').addEventListener('click', loadTransactions);

// Initialize on page load
updateAuthUI();