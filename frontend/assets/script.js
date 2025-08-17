document.addEventListener("DOMContentLoaded", async () => {
  const loginForm = document.getElementById('loginForm');
  const otpModal = document.getElementById('otpModal');
  const otpForm = document.getElementById('otpForm');
  const otpMessage = document.getElementById('otpMessage');
  let device_id = null;

  // 📌 Load FingerprintJS for device ID
  try {
    const FingerprintJS = await import('https://openfpcdn.io/fingerprintjs/v3');
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    device_id = result.visitorId;
    console.log("🖥️ Device ID (FingerprintJS):", device_id);
  } catch (err) {
    console.warn("⚠️ Failed to load FingerprintJS:", err);
  }

  // ----- LOGIN -----
  if (loginForm) {
    console.log("Login form loaded.");
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const role = document.getElementById('role').value;

      const payload = {
        username,
        password,
        role,
        device_id // 👉 send device ID
      };

      const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();

      if (result.success) {
        localStorage.setItem("username", username);
        if (role === 'admin') {
          window.location.href = 'admin.html';
        } else {
          window.location.href = 'dashboard.html';
        }
      } else if (result.require_otp) {
        localStorage.setItem("username", username);

        // 🔐 Trigger OTP email
        await fetch('/request-login-otp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username })
        });

        if (otpModal) otpModal.style.display = 'block';
      } else {
        document.getElementById('loginMessage').innerText = result.message || 'Login failed.';
      }
    });
  }

  // ----- OTP Verification -----
  if (otpForm) {
    otpForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = localStorage.getItem("username");
      const otp = document.getElementById('otpInput').value;

      const res = await fetch('/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, otp })
      });

      const result = await res.json();
      if (result.success) {
        otpMessage.style.color = "green";
        otpMessage.innerText = result.message;
        setTimeout(() => {
          window.location.href = 'dashboard.html';
        }, 1500);
      } else {
        otpMessage.style.color = "red";
        otpMessage.innerText = result.message;
      }
    });
  }

  // ----- REGISTER -----
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    console.log("Register form loaded.");
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirmPassword').value;
      const role = document.getElementById('role').value;
      const pin = document.getElementById('pin').value;
      const email = document.getElementById('email').value;
      const msg = document.getElementById('registerMessage');

      if (password !== confirmPassword) {
        msg.innerText = "Passwords do not match.";
        msg.style.color = "red";
        return;
      }

      if (!/^\d{4,6}$/.test(pin)) {
        msg.innerText = "PIN must be 4 to 6 digits.";
        msg.style.color = "red";
        return;
      }

      const response = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role, pin, email })
      });

      const result = await response.json();
      console.log("Registration result:", result);

      if (result.success) {
        msg.style.color = "green";
        msg.innerText = result.message || "Registration successful! Redirecting to login...";
        console.log("✅ Registration successful, redirecting in 2 seconds...");
        setTimeout(() => {
          console.log("🔁 Redirecting now...");
          window.location.href = 'login.html';
        }, 2000);
      } else {
        msg.style.color = "red";
        msg.innerText = result.message || "Registration failed.";
      }
    });
  }
});
