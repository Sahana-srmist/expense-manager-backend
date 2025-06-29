const BASE_URL = "http://127.0.0.1:8000";

async function register() {
  const username = document.getElementById("reg-username").value;
  const password = document.getElementById("reg-password").value;

  try {
    const res = await fetch(`${BASE_URL}/register?username=${username}&password=${password}`, {
      method: "POST"
    });

    const data = await res.json();

    if (res.ok) {
      alert("Registration successful! You can now log in.");
      location.href = "login.html";
    } else {
      alert(data.detail || "Registration failed");
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function login() {
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  const token = btoa(`${username}:${password}`);

  try {
    const res = await fetch(`${BASE_URL}/login`, {
      method: "POST",
      headers: {
        Authorization: "Basic " + token
      }
    });

    if (res.ok) {
      alert("Login successful!");
      localStorage.setItem("auth", token);
      localStorage.setItem("username", username);
      location.href = "dashboard.html";
    } else {
      const data = await res.json();
      alert("Login failed: " + data.detail);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

async function addExpense() {
  const reason = document.getElementById("reason").value;
  const amount = parseFloat(document.getElementById("amount").value);
  const date = document.getElementById("date").value;

  const token = localStorage.getItem("auth");
  const username = localStorage.getItem("username");

  const res = await fetch(`${BASE_URL}/add`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Basic " + token
    },
    body: JSON.stringify({ username, reason, amount, date })
  });

  if (res.ok) {
    alert("Expense added successfully!");
    document.getElementById("reason").value = "";
    document.getElementById("amount").value = "";
    document.getElementById("date").value = "";
  } else {
    const err = await res.json();
    alert("Error: " + err.detail);
  }
}

async function getAllExpenses() {
  const token = localStorage.getItem("auth");
  const res = await fetch(`${BASE_URL}/expenses`, {
    headers: { Authorization: "Basic " + token }
  });

  if (res.ok) {
    const data = await res.json();
    createTable(data);
  } else {
    document.getElementById("output").innerText = "No expenses found.";
  }
}

async function searchByReason() {
  const token = localStorage.getItem("auth");
  const reason = document.getElementById("search-reason").value;
  const res = await fetch(`${BASE_URL}/search/?reason=${reason}`, {
    headers: { Authorization: "Basic " + token }
  });

  if (res.ok) {
    const data = await res.json();
    createTable(data);
  } else {
    document.getElementById("output").innerText = "No matching expenses.";
  }
}

async function searchByDate() {
  const token = localStorage.getItem("auth");
  const date = document.getElementById("search-date").value;
  const res = await fetch(`${BASE_URL}/search/date?date=${date}`, {
    headers: { Authorization: "Basic " + token }
  });

  if (res.ok) {
    const data = await res.json();
    createTable(data);
  } else {
    document.getElementById("output").innerText = "No expenses on this date.";
  }
}

async function getSummary() {
  const token = localStorage.getItem("auth");
  const res = await fetch(`${BASE_URL}/summary`, {
    headers: { Authorization: "Basic " + token }
  });

  if (res.ok) {
    const data = await res.json();
    let html = `
      <p><strong>Total:</strong> ₹${data.total_expense}</p>
      <p><strong>Average:</strong> ₹${data.average_expense}</p>
      <p><strong>Highest:</strong> ₹${data.highest_expense} on ${data.highest_date}</p>
      <p><strong>Lowest:</strong> ₹${data.lowest_expense} on ${data.lowest_date}</p>
      <p><strong>Records:</strong> ${data.records}</p>
    `;

    document.getElementById("output").innerHTML = html;
  } else {
    document.getElementById("output").innerText = "Unable to fetch summary.";
  }
}

async function getMonthlySummary() {
  const token = localStorage.getItem("auth");
  const month = document.getElementById("month").value;
  const year = document.getElementById("year").value;

  const monthNum = parseInt(month);
  const yearNum = parseInt(year);

  if (!month || !year || isNaN(monthNum) || isNaN(yearNum) || monthNum < 1 || monthNum > 12 || yearNum < 1000 || yearNum > 9999) {
    alert("Please enter a valid month (1–12) and a valid 4-digit year.");
    return;
  }

  const res = await fetch(`${BASE_URL}/summary/monthly?month=${monthNum}&year=${yearNum}`, {
    headers: { Authorization: "Basic " + token }
  });

  if (res.ok) {
    const data = await res.json();
    let html = `
      <p><strong>Month:</strong> ${data.month}</p>
      <p><strong>Total:</strong> ₹${data.total}</p>
      <p><strong>Average:</strong> ₹${data.average}</p>
      <p><strong>Highest:</strong> ₹${data.highest}</p>
      <p><strong>Lowest:</strong> ₹${data.lowest}</p>
      <p><strong>Count:</strong> ${data.count}</p>
    `;
    document.getElementById("output").innerHTML = html;
  } else {
    const err = await res.json();
    document.getElementById("output").innerText = "Error: " + err.detail;
  }
}

function downloadCSV() {
  const username = localStorage.getItem("username");
  const url = `${BASE_URL}/export/csv`;

  const a = document.createElement("a");
  a.href = url;
  a.download = `${username}_expenses.csv`;
  a.setAttribute("target", "_blank");
  a.click();
}

function downloadChart() {
  const username = localStorage.getItem("username");
  const url = `${BASE_URL}/export/bar-chart`;

  const a = document.createElement("a");
  a.href = url;
  a.download = `${username}_expenses_bar_chart.png`;
  a.setAttribute("target", "_blank");
  a.click();
}

async function deleteExpense() {
  const token = localStorage.getItem("auth");
  const reason = document.getElementById("del-reason").value;

  const res = await fetch(`${BASE_URL}/delete/?reason=${reason}`, {
    method: "DELETE",
    headers: { Authorization: "Basic " + token }
  });

  if (res.ok) {
    const data = await res.json();
    document.getElementById("output").innerText = data.message;
  } else {
    const err = await res.json();
    document.getElementById("output").innerText = "Error: " + err.detail;
  }
}

function updateAuthButton() {
  const btn = document.getElementById("auth-button");
  const username = localStorage.getItem("username");
  if (btn) {
    btn.textContent = username ? "Logout" : "Login";
  }
}

function handleAuth() {
  const username = localStorage.getItem("username");
  if (username) {
    localStorage.clear();
    alert("You have been logged out.");
    location.href = "index.html"; // ✅ Now redirects to homepage
  } else {
    location.href = "login.html";
  }
}

function createTable(data) {
  if (data.length === 0) {
    document.getElementById("output").innerText = "No data found.";
    return;
  }

  let html = "<table border='1' style='margin: 20px auto; border-collapse: collapse;'>";
  html += "<tr><th>Reason</th><th>Amount</th><th>Date</th></tr>";

  data.forEach(item => {
    html += `
      <tr>
        <td>${item.reason}</td>
        <td>₹${item.amount}</td>
        <td>${item.date}</td>
      </tr>
    `;
  });

  html += "</table>";
  document.getElementById("output").innerHTML = html;
}

// ✅ Initialize when script loads
updateAuthButton();

function capitalizeName(name) {
  return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
}

function updateNavbar() {
  const username = localStorage.getItem("username");
  const authBtn = document.getElementById("auth-button");
  const userInfo = document.getElementById("user-info");
  const path = window.location.pathname;

  if (username) {
    // Logged in
    authBtn.textContent = "Logout";
    authBtn.onclick = () => {
      localStorage.clear();
      alert("You have been logged out.");
      location.href = "index.html";
    };
    if (userInfo) {
      userInfo.style.display = "block";
      document.getElementById("nav-username").textContent = capitalizeName(username);
    }
  } else {
    // Not logged in
    if (userInfo) userInfo.style.display = "none";

    if (path.includes("login.html")) {
      authBtn.textContent = "Go to Register";
      authBtn.onclick = () => location.href = "register.html";
    } else if (path.includes("register.html")) {
      authBtn.textContent = "Go to Login";
      authBtn.onclick = () => location.href = "login.html";
    } else {
      authBtn.textContent = "Login";
      authBtn.onclick = () => location.href = "login.html";
    }
  }
}

function handleAuth() {
  const username = localStorage.getItem("username");
  if (username) {
    localStorage.clear();
    alert("You have been logged out.");
    location.href = "index.html";
  } else {
    location.href = "login.html";
  }
}
// ✅ Call this on every page to update the navbar
window.addEventListener("DOMContentLoaded", updateNavbar);
