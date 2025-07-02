const BASE_URL = "https://expense-manager-backend-i32b.onrender.com";

// ------------------------ AUTH ------------------------
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

// ------------------------ EXPENSE ACTIONS ------------------------
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

async function deleteBySno(sno) {
  if (!confirm(`Are you sure you want to delete this expense?`)) return;

  showLoader();
  const token = localStorage.getItem("auth");

  try {
    const res = await fetch(`${BASE_URL}/delete/sno/${sno}`, {
      method: "DELETE",
      headers: {
        Authorization: "Basic " + token
      }
    });

    const msg = await res.json();
    alert(msg.message);
    loadExpenses();
  } catch (err) {
    alert("Failed: " + err.message);
  } finally {
    hideLoader();
  }
}

// ------------------------ FILTER / SEARCH ------------------------
async function loadExpenses() {
  showLoader();
  const token = localStorage.getItem("auth");

  try {
    const res = await fetch(`${BASE_URL}/expenses`, {
      headers: { Authorization: "Basic " + token }
    });

    const data = await res.json();
    createTable(data);
    document.getElementById("reset-section").style.display = "none";
  } catch (err) {
    document.getElementById("expense-body").innerHTML = `
      <tr><td colspan="4" style="text-align:center; padding: 10px; color:red;">Failed to load data</td></tr>`;
  } finally {
    hideLoader();
  }
}

async function searchByReason() {
  showLoader();
  const token = localStorage.getItem("auth");
  const reason = document.getElementById("search-reason").value;

  try {
    const res = await fetch(`${BASE_URL}/search/?reason=${reason}`, {
      headers: { Authorization: "Basic " + token }
    });

    const data = await res.json();
    createTable(data);
    document.getElementById("reset-section").style.display = "block";
  } catch {
    alert("Error searching by reason");
  } finally {
    hideLoader();
  }
}

async function searchByDate() {
  showLoader();
  const token = localStorage.getItem("auth");
  const date = document.getElementById("search-date").value;

  try {
    const res = await fetch(`${BASE_URL}/search/date?date=${date}`, {
      headers: { Authorization: "Basic " + token }
    });

    const data = await res.json();
    createTable(data);
    document.getElementById("reset-section").style.display = "block";
  } catch {
    alert("Error searching by date");
  } finally {
    hideLoader();
  }
}

// ------------------------ SUMMARY ------------------------
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
    const outputDiv = document.getElementById("output");
    if (outputDiv) outputDiv.innerHTML = html;
  } else {
    const outputDiv = document.getElementById("output");
    if (outputDiv) outputDiv.innerText = "Unable to fetch summary.";
  }
}


// ------------------------ EXPORT ------------------------
function downloadCSV() {
  const username = localStorage.getItem("username");
  const url = `${BASE_URL}/export/csv`;

  const a = document.createElement("a");
  a.href = url;
  a.download = `${username}_expenses.csv`;
  a.setAttribute("target", "_blank");
  a.click();
}

// ------------------------ DELETE BY REASON ------------------------
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

// ------------------------ UI HELPERS ------------------------
function createTable(data) {
  const tbody = document.getElementById("expense-body");
  tbody.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 10px;">No data found.</td></tr>`;
    return;
  }

  data.forEach(exp => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td style="padding: 10px; border-bottom: 1px solid #ddd;">${exp.date}</td>
      <td style="padding: 10px; border-bottom: 1px solid #ddd;">${exp.reason}</td>
      <td style="padding: 10px; border-bottom: 1px solid #ddd;">₹${exp.amount}</td>
      <td style="padding: 10px; border-bottom: 1px solid #ddd;">
        <button onclick="deleteBySno(${exp.sno})" style="background-color: #795548; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer;">
          Delete
        </button>
      </td>`;
    tbody.appendChild(row);
  });
}

function capitalizeName(name) {
  return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
}

function updateAuthButton() {
  const btn = document.getElementById("auth-button");
  const username = localStorage.getItem("username");
  if (btn) {
    btn.textContent = username ? "Logout" : "Login";
  }
}

function updateNavbar() {
  try {
    const username = localStorage.getItem("username");
    const authBtn = document.getElementById("auth-button");
    const userInfo = document.getElementById("user-info");

    if (!authBtn) return; // navbar not ready yet

    const path = window.location.pathname;

    if (username) {
      authBtn.textContent = "Logout";
      authBtn.onclick = handleAuth;

      if (userInfo) {
        userInfo.style.display = "block";
        const navUser = document.getElementById("nav-username");
        if (navUser) navUser.textContent = capitalizeName(username);
      }
    } else {
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
  } catch (err) {
    console.warn("updateNavbar failed:", err);
  }
}


window.addEventListener("DOMContentLoaded", updateNavbar);

function toggleSearch(type) {
  const reasonBox = document.getElementById("reason-search");
  const dateBox = document.getElementById("date-search");

  if (type === "reason") {
    reasonBox.style.display = "block";
    dateBox.style.display = "none";
  } else if (type === "date") {
    reasonBox.style.display = "none";
    dateBox.style.display = "block";
  }
}

//-------------------Show Bar Chart--------------//

async function showChart() {
  console.log("showChart called");

  const res = await fetch(`${BASE_URL}/export/bar-chart`, {
    headers: { Authorization: "Basic " + localStorage.getItem("auth") }
  });

  console.log("response.ok?", res.ok);

  if (res.ok) {
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    const chartContainer = document.getElementById("chart-container");
    chartContainer.innerHTML = "";

    const img = document.createElement("img");
    img.src = url;
    img.id = "chart-image";
    img.style.maxWidth = "90%";
    img.style.display = "block";

    chartContainer.appendChild(img);
    console.log("Chart appended");

    // Enable download button here
    const downloadBtn = document.getElementById("download-chart-btn");
    if (downloadBtn) {
      downloadBtn.style.display = "inline-block"; // Show the button
    }
  } else {
    console.log("Chart fetch failed");
  }
}


function downloadChart() {
  const chart = document.getElementById("chart-image");

  if (chart) {
    const link = document.createElement("a");
    link.href = chart.src;
    link.download = "expense_chart.png";
    link.click();
  } else {
    alert("Please click 'Show Bar Chart' first.");
  }
}


// ------------------------ Loading Spinner ------------------------
function showLoader() {
  const loader = document.getElementById("loader");
  if (loader) loader.style.display = "block";
}

function hideLoader() {
  const loader = document.getElementById("loader");
  if (loader) loader.style.display = "none";
}
document.addEventListener("DOMContentLoaded", () => {
  const chartBtn = document.getElementById("chart-btn");
  if (chartBtn) {
    chartBtn.addEventListener("click", function (e) {
      e.preventDefault();       // PREVENT RELOAD
      showChart();              // CALL THE FUNCTION
    });
  }
});
