const CURRENT_USER = localStorage.getItem("username");

const userSearchInput = document.getElementById("userSearch");
const userResults = document.getElementById("userResults");
const transactionForm = document.getElementById("transactionForm");
const amountInput = document.getElementById("amount");
const secretKeyField = document.getElementById("secretKeyField");
const secretKeyInput = document.getElementById("secretKey");
const transactionTypeInput = document.getElementById("transactionType");
const feedback = document.getElementById("feedback");

let users = [];
let geo_lat = null;
let geo_lon = null;
let ip_address = null;
let device_id = null;
let locationReady = false;

// Redirect if not logged in
if (!CURRENT_USER) {
  alert("You must be logged in to use this page.");
  window.location.href = "/login.html";
}

// Fetch user list
fetch("/users")
  .then(res => res.json())
  .then(data => users = data.users || [])
  .catch(err => console.error("User list fetch failed", err));

// Get IP address
fetch("https://api.ipify.org?format=json")
  .then(res => res.json())
  .then(data => {
    ip_address = data.ip;
    console.log("🌐 IP Address:", ip_address);
  })
  .catch(err => console.warn("Failed to fetch IP address", err));

// Load FingerprintJS for device_id
import('https://openfpcdn.io/fingerprintjs/v3')
  .then(FingerprintJS => FingerprintJS.load())
  .then(fp => fp.get())
  .then(result => {
    device_id = result.visitorId;
    console.log("🖥️ Device ID (FingerprintJS):", device_id);
  })
  .catch(err => console.warn("Failed to load FingerprintJS", err));

// Get geolocation (required)
navigator.geolocation.getCurrentPosition(
  pos => {
    geo_lat = pos.coords.latitude;
    geo_lon = pos.coords.longitude;
    locationReady = true;
    console.log("📍 Location ready:", geo_lat, geo_lon);
  },
  err => {
    console.warn("⚠️ Geolocation error:", err.message);
    alert("❌ Location access is required to complete transactions.");
    locationReady = false;
  },
  { enableHighAccuracy: true }
);

// Autocomplete recipient dropdown
userSearchInput.addEventListener("input", () => {
  const query = userSearchInput.value.trim().toLowerCase();
  userResults.innerHTML = "";

  const matches = users.filter(user => user.toLowerCase().includes(query));
  if (!query || matches.length === 0) {
    userResults.classList.add("hidden");
    return;
  }

  matches.forEach(user => {
    const li = document.createElement("li");
    li.textContent = user;
    li.className = "p-2 hover:bg-gray-100 cursor-pointer";
    li.onclick = () => {
      userSearchInput.value = user;
      userResults.innerHTML = "";
      userResults.classList.add("hidden");
    };
    userResults.appendChild(li);
  });

  userResults.classList.remove("hidden");
});

document.addEventListener("click", (e) => {
  if (!document.querySelector(".search-container").contains(e.target)) {
    userResults.classList.add("hidden");
  }
});

// Reset secret key field on amount change
amountInput.addEventListener("input", () => {
  secretKeyField.classList.add("hidden");
  secretKeyInput.value = "";
});

// Handle form submission
transactionForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!locationReady || geo_lat === null || geo_lon === null) {
    showFeedback("📍 Location permission required. Please allow access.", "text-yellow-600");
    return;
  }

  const sender = CURRENT_USER;
  const recipient = userSearchInput.value.trim();
  const amount = parseFloat(amountInput.value);
  const transaction_type = transactionTypeInput.value;
  const secretKey = secretKeyInput.value.trim();
  const timestamp = new Date().toISOString();

  if (!recipient || isNaN(amount) || !transaction_type) {
    showFeedback("Please complete all required fields.", "text-red-600");
    return;
  }

  const payload = {
    sender_id: sender,
    recipient_id: recipient,
    amount,
    transaction_type,
    timestamp,
    device_id,
    geo_lat,
    geo_lon,
    ip_address
  };

  if (secretKey) payload.pin = secretKey;

  console.log("📤 Sending payload:", payload);

  try {
    const res = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();

    if (!res.ok || result.error) {
      const msg = result.error || "Something went wrong.";
      showFeedback(`❌ ${msg}`, "text-red-600");
      return;
    }

    if (result.is_fraud === 0) {
      showFeedback("✅ Transaction Successful.", "text-green-600");
      transactionForm.reset();
      secretKeyField.classList.add("hidden");
      return setTimeout(() => location.href = "dashboard.html", 1500);
    }

    if (amount >= 1000) {
      showFeedback("❌ High-risk transaction blocked. Logging out...", "text-red-600");
      await logFraudAlert(sender, amount, "Fraudulent", "Model flagged high-value fraud.");
    
      // Clear local session and redirect
      setTimeout(() => {
        localStorage.removeItem("username");
        window.location.href = "login.html";
      }, 2000);
    
      return;
    }
    

    if (!secretKey) {
      secretKeyField.classList.remove("hidden");
      showFeedback("⚠️ Fraud detected. Enter secret key to override.", "text-yellow-600");
      return;
    }
    
    // ⚠️ NEW: Handle incorrect PIN case (logout)
    if (result.logout) {
      showFeedback("❌ " + result.message, "text-red-600");
      localStorage.removeItem("username");
      setTimeout(() => {
        window.location.href = "login.html";
      }, 2000);
      return;
    }
    
    // ✅ If override accepted
    if (result.allowed) {
      showFeedback("✅ Transaction completed after override.", "text-green-600");
      await logFraudAlert(sender, amount, "Fraudulent", "Transaction overridden with secret key.");
      transactionForm.reset();
      secretKeyField.classList.add("hidden");
      setTimeout(() => location.href = "dashboard.html", 1500);
      return;
    }
    
    // 🔒 Final fallback
    showFeedback("❌ Transaction blocked due to fraud risk.", "text-red-600");
    
  } catch (err) {
    console.error("Prediction failed", err);
    showFeedback("Something went wrong. Please try again.", "text-red-600");
  }
});

// Feedback helper
function showFeedback(message, className) {
  feedback.textContent = message;
  feedback.className = `feedback ${className}`;
}

// Log alerts to backend
async function logFraudAlert(user, amount, status, details) {
  await fetch("/log_alert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user,
      id: "ALRT" + Math.floor(100000 + Math.random() * 900000),
      amount,
      status,
      timestamp: new Date().toISOString(),
      details
    })
  });
}
