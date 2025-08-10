// Upload CSV
document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("csvFile");
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const res = await fetch("http://localhost:5000/upload", {
    method: "POST",
    body: formData
  });

  const result = await res.json();
  document.getElementById("uploadStatus").innerText = result.message || "Upload complete.";
});

// Train model
document.getElementById("trainBtn").addEventListener("click", async () => {
  const res = await fetch("http://localhost:5000/train", { method: "POST" });
  const result = await res.json();
  document.getElementById("trainStatus").innerText = result.message || "Model training finished.";
});

// Load fraud alerts
document.getElementById("loadAlerts").addEventListener("click", async () => {
  const res = await fetch("http://localhost:5000/alerts");
  const result = await res.json();
  const tbody = document.querySelector("#alertsTable tbody");
  tbody.innerHTML = "";

  result.alerts.forEach(alert => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${alert.id}</td><td>${alert.amount}</td><td>${alert.status}</td>`;
    tbody.appendChild(row);
  });
});
