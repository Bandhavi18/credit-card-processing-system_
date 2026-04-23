const API_BASE = "http://127.0.0.1:5000/api";
let currentUser = JSON.parse(sessionStorage.getItem("user"));

async function registerUser() {
  const name = document.getElementById("regName").value;
  const email = document.getElementById("regEmail").value;
  const password = document.getElementById("regPassword").value;

  const res = await fetch(`${API_BASE}/register`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ name, email, password })
  });

  const data = await res.json();
  document.getElementById("message").innerText = data.message;
}

async function loginUser() {
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;

  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();
  document.getElementById("message").innerText = data.message;

  if (res.ok) {
    sessionStorage.setItem("user", JSON.stringify(data.user));
    window.location.href = "dashboard.html";
  }
}

async function createTransaction() {
  const user = JSON.parse(sessionStorage.getItem("user"));
  const cardholder_name = document.getElementById("cardholderName").value;
  const masked_card = document.getElementById("maskedCard").value;
  const amount = document.getElementById("amount").value;
  const reference = document.getElementById("reference").value;
  const mode = document.getElementById("networkMode").value;

  const res = await fetch(`${API_BASE}/transactions`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      merchant_id: user.id,
      cardholder_name,
      masked_card,
      amount,
      reference,
      mode
    })
  });

  const data = await res.json();
  document.getElementById("dashboardMessage").innerText = data.message || data.status;
  loadTransactions();
  loadLogs();
}

async function syncTransactions() {
  const res = await fetch(`${API_BASE}/sync`, {
    method: "POST"
  });

  const data = await res.json();
  document.getElementById("dashboardMessage").innerText = data.message;
  loadTransactions();
  loadLogs();
}

async function loadTransactions() {
  const res = await fetch(`${API_BASE}/transactions`);
  const data = await res.json();

  const table = document.getElementById("transactionTable");
  if (!table) return;

  table.innerHTML = "";
  data.forEach(txn => {
    table.innerHTML += `
      <tr>
        <td>${txn.transaction_id}</td>
        <td>${txn.merchant_name}</td>
        <td>₹${txn.amount}</td>
        <td>${txn.status}</td>
        <td>${txn.mode}</td>
        <td>${txn.created_at}</td>
      </tr>
    `;
  });
}

async function loadLogs() {
  const res = await fetch(`${API_BASE}/logs`);
  const data = await res.json();

  const logList = document.getElementById("logList");
  if (!logList) return;

  logList.innerHTML = "";
  data.forEach(log => {
    logList.innerHTML += `<li>${log.created_at} - ${log.action} - ${log.details}</li>`;
  });
}

window.onload = function () {
  if (window.location.pathname.includes("dashboard.html")) {
    const user = JSON.parse(sessionStorage.getItem("user"));
    if (!user) {
      window.location.href = "index.html";
      return;
    }
    document.getElementById("userName").innerText = user.name;
    loadTransactions();
    loadLogs();
  }
};