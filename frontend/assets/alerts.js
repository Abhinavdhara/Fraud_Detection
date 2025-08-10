const currentUser = localStorage.getItem("username");

fetch("http://localhost:5000/alerts")
  .then((response) => response.json())
  .then((data) => {
    const allAlerts = data.alerts || [];
    const alerts = allAlerts.filter(alert => alert.user === currentUser);
    const alertsList = document.getElementById("alertsList");

    if (alerts.length === 0) {
      alertsList.innerHTML = "<p>No alerts found for your account.</p>";
      return;
    }

    alerts.forEach((alert) => {
      const div = document.createElement("div");
      div.className = "alert";

      const isBypassed = alert.details && alert.details.toLowerCase().includes("bypassed");

      div.innerHTML = `
        <div class="header">
          Alert ID: ${alert.id || "N/A"} - ${alert.status}
          ${isBypassed ? "<span style='color: orange;'>(Overridden)</span>" : ""}
        </div>
        <div class="meta">Amount: $${alert.amount} | ${new Date(alert.timestamp).toLocaleString()}</div>
        ${
          alert.details
            ? `<div class="details" style="display:none; margin-top:10px; color:#333;">${alert.details}</div>`
            : ""
        }
      `;

      div.addEventListener("click", () => {
        const detailDiv = div.querySelector(".details");
        if (detailDiv) {
          detailDiv.style.display = detailDiv.style.display === "none" ? "block" : "none";
        }
      });

      alertsList.appendChild(div);
    });
  })
  .catch((error) => {
    console.error("Failed to fetch alerts:", error);
    document.getElementById("alertsList").innerHTML = "<p>Error loading alerts.</p>";
  });
