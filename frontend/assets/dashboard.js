document.addEventListener("DOMContentLoaded", async () => {
    
  
    const currentUser = localStorage.getItem("username");
    if (!currentUser) {
      window.location.href = "login.html";
      return;
    }
  
    // Fetch dashboard stats and recent transactions
    fetchStats();
    loadTransactionHistory();
  
    // Handle transaction form submit
    const form = document.getElementById("transactionForm");
    if (form) {
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
  
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
          data[key] = isNaN(value) ? value : parseFloat(value);
        }
  
        const statusEl = document.getElementById("transactionStatus");
        statusEl.textContent = "Checking transaction...";
  
        try {
          const res = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
          });
  
          const result = await res.json();
          if (result.prediction) {
            statusEl.textContent = `🚨 Prediction: ${result.prediction}`;
            fetchStats();
            loadTransactionHistory();
          } else if (result.error) {
            statusEl.textContent = `❌ Error: ${result.error}`;
          } else {
            statusEl.textContent = "⚠️ Unexpected response.";
          }
        } catch (err) {
          statusEl.textContent = "⚠️ Failed to connect to server.";
          console.error(err);
        }
      });
    }
  
    // New Transaction button navigation
    const newTxnBtn = document.getElementById("newTransactionBtn");
    if (newTxnBtn) {
      newTxnBtn.addEventListener("click", () => {
        window.location.href = "transaction.html";
      });
    }
  
    // Setup OTP modal logic
    setupOtpModal();
  });
  
  
  
  // Fetch and update fraud stats & total transactions
  async function fetchStats() {
    const currentUser = localStorage.getItem("username");
    if (!currentUser) return;
  
    try {
      const [alertsRes, txRes] = await Promise.all([
        fetch(`/alerts?username=${currentUser}`),
        fetch(`/transactions?user=${currentUser}`)
      ]);
  
      const alertsData = await alertsRes.json();
      const txData = await txRes.json();
  
      const alerts = alertsData.alerts || [];
      const transactions = txData.transactions || [];
  
      let fraudCount = 0;
      alerts.forEach(a => {
        if (a.status === "Fraudulent") fraudCount++;
      });
  
      const lastTransaction = transactions.length ? transactions[transactions.length - 1] : null;
  
      document.getElementById("fraudCount").textContent = fraudCount;
  
      // Filter only transactions involving current user
      const relevantTxs = transactions.filter(
        tx => tx.sender === currentUser || tx.recipient === currentUser
      );
      document.getElementById("totalTransactions").textContent = relevantTxs.length;
  
      document.getElementById("lastTransaction").textContent = lastTransaction
        ? `₹${lastTransaction.amount.toFixed(2)} on ${new Date(lastTransaction.timestamp).toLocaleDateString()}`
        : "-";
  
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }
  }
  
  // Load recent transactions (last 5)
  async function loadTransactionHistory() {
    const currentUser = localStorage.getItem("username");
    if (!currentUser) return;
  
    try {
      const res = await fetch(`/transactions?user=${currentUser}`);
      const data = await res.json();
      const transactions = data.transactions || [];
  
      const tableBody = document.getElementById("recentTransactionsBody");
      if (!tableBody) return;
  
      tableBody.innerHTML = "";
  
      transactions.slice(-5).reverse().forEach(tx => {
        const isCredit = tx.recipient === currentUser;
        const isDebit = tx.sender === currentUser;
  
        if (!isCredit && !isDebit) return;
  
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${tx.id}</td>
          <td style="color: ${isCredit ? 'green' : 'red'}">${isCredit ? '+' : '-'}₹${parseFloat(tx.amount).toFixed(2)}</td>
          <td>${tx.status}</td>
          <td>${new Date(tx.timestamp).toLocaleString()}</td>
          <td>${isCredit ? tx.sender : tx.recipient}</td>
        `;
        tableBody.appendChild(row);
      });
    } catch (err) {
      console.error("Failed to load transaction history:", err);
    }
  }
  
  // Setup OTP modal event listeners and logic
  function setupOtpModal() {
    const showBalanceBtn = document.getElementById("showBalanceBtn");
    const otpModal = document.getElementById("otpModal");
    const verifyOtpBtn = document.getElementById("verifyOtpBtn");
    const otpInput = document.getElementById("otpInput");
    const otpStatus = document.getElementById("otpStatus");
    const closeOtpBtn = document.getElementById("closeOtpModal");
  
    if (showBalanceBtn && otpModal && verifyOtpBtn && otpInput && otpStatus && closeOtpBtn) {
      showBalanceBtn.addEventListener("click", async () => {
        otpStatus.textContent = "";
        otpInput.value = "";
  
        otpModal.style.display = "flex";
        otpStatus.textContent = "Loading...";
  
        try {
          const res = await fetch("/request-otp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: localStorage.getItem("username") }),
          });
  
          const data = await res.json();
          if (data.success) {
            otpStatus.style.color = "green";
            otpStatus.textContent = "OTP sent to your email.";
          } else {
            otpStatus.style.color = "red";
            otpStatus.textContent = data.error || "Failed to send OTP.";
          }
        } catch (err) {
          otpStatus.style.color = "red";
          otpStatus.textContent = "Error sending OTP.";
          console.error(err);
        }
      });
  
      verifyOtpBtn.addEventListener("click", async () => {
        const otp = otpInput.value.trim();
        if (!otp) {
          otpStatus.textContent = "Please enter the OTP.";
          return;
        }
  
        try {
          const res = await fetch("/verify-pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: localStorage.getItem("username"), otp }),
          });
  
          const data = await res.json();
          if (data.success && data.balance !== undefined) {
            document.getElementById("hiddenBalance").textContent = `₹${data.balance.toFixed(2)}`;
            otpModal.style.display = "none";
          } else {
            otpStatus.style.color = "red";
            otpStatus.textContent = data.error || "Invalid OTP.";
          }
        } catch (err) {
          otpStatus.style.color = "red";
          otpStatus.textContent = "Error verifying OTP.";
          console.error(err);
        }
      });
  
      closeOtpBtn.addEventListener("click", () => {
        otpModal.style.display = "none";
      });
  
      window.addEventListener("click", (e) => {
        if (e.target === otpModal) {
          otpModal.style.display = "none";
        }
      });
    }
  }
  

