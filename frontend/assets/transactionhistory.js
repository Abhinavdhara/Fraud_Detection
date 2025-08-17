document.addEventListener("DOMContentLoaded", async () => {
  const currentUser = localStorage.getItem("username");
  if (!currentUser) return void (window.location.href = "login.html");

  // Load sidebar profile info
  try {
    const res = await fetch(`/profile?username=${currentUser}`);
    const data = await res.json();
    if (data.success) {
      const { username, role } = data.profile;
      document.getElementById("profileUsername").textContent = username;
      document.getElementById("profileRole").textContent = role;
      document.getElementById("profileAvatar").textContent = username.charAt(0).toUpperCase();
    }
  } catch (err) {
    console.error("Failed to load profile info:", err);
  }

  const tableBody = document.getElementById("allTransactionsBody");
  const monthFilter = document.getElementById("monthFilter");
  const searchInput = document.getElementById("searchInput");
  const clearFiltersBtn = document.getElementById("clearFiltersBtn");

  const totalCountEl = document.getElementById("totalCount");
  const totalCreditEl = document.getElementById("totalCredit");
  const totalDebitEl = document.getElementById("totalDebit");

  let allTransactions = [];

  try {
    const res = await fetch(`/transactions?user=${currentUser}`);
    const data = await res.json();
    allTransactions = data.transactions || [];
    populateMonthOptions(allTransactions);
    renderTransactions(allTransactions);
  } catch (err) {
    console.error("Failed to load transactions:", err);
    tableBody.innerHTML = "<tr><td colspan='5'>Error loading transactions.</td></tr>";
  }

  function populateMonthOptions(transactions) {
    const months = new Set(
      transactions.map(tx => new Date(tx.timestamp).toLocaleString("default", { month: "long", year: "numeric" }))
    );

    [...months]
      .sort((a, b) => new Date("1 " + b) - new Date("1 " + a))
      .forEach(month => {
        const option = document.createElement("option");
        option.value = month;
        option.textContent = month;
        monthFilter.appendChild(option);
      });
  }

  function renderTransactions(transactions) {
    tableBody.innerHTML = "";
    if (!transactions.length) {
      tableBody.innerHTML = "<tr><td colspan='5'>No transactions found.</td></tr>";
      updateSummary([]);
      return;
    }

    transactions.slice().reverse().forEach(tx => {
      const isCredit = tx.recipient === currentUser;
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${tx.id}</td>
        <td style="color: ${isCredit ? "green" : "red"}">${isCredit ? "+" : "-"}₹${parseFloat(tx.amount).toFixed(2)}</td>
        <td>${tx.status}</td>
        <td>${new Date(tx.timestamp).toLocaleString()}</td>
        <td>${isCredit ? tx.sender : tx.recipient}</td>
      `;
      tableBody.appendChild(row);
    });
    updateSummary(transactions);
  }

  function updateSummary(transactions) {
    const credit = transactions.reduce((sum, tx) => (tx.recipient === currentUser ? sum + tx.amount : sum), 0);
    const debit = transactions.reduce((sum, tx) => (tx.sender === currentUser ? sum + tx.amount : sum), 0);

    totalCountEl.textContent = transactions.length;
    totalCreditEl.textContent = `₹${credit.toFixed(2)}`;
    totalDebitEl.textContent = `₹${debit.toFixed(2)}`;
  }

  function applyFilters() {
    let filtered = [...allTransactions];

    if (monthFilter.value !== "all") {
      filtered = filtered.filter(tx => {
        const month = new Date(tx.timestamp).toLocaleString("default", { month: "long", year: "numeric" });
        return month === monthFilter.value;
      });
    }

    const query = searchInput.value.toLowerCase().trim();
    if (query) {
      filtered = filtered.filter(tx => {
        const counterparty = tx.recipient === currentUser ? tx.sender : tx.recipient;
        return counterparty.toLowerCase().includes(query);
      });
    }

    renderTransactions(filtered);
  }

  monthFilter.addEventListener("change", applyFilters);
  searchInput.addEventListener("input", applyFilters);
  clearFiltersBtn.addEventListener("click", () => {
    monthFilter.value = "all";
    searchInput.value = "";
    renderTransactions(allTransactions);
  });

  // Logout and avatar initials
  document.getElementById("logoutBtn")?.addEventListener("click", () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "login.html";
  });

  const profileAvatarEl = document.getElementById("profileAvatar");
  if (profileAvatarEl) profileAvatarEl.textContent = currentUser.charAt(0).toUpperCase();
});
