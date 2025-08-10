// sidebar.js
document.addEventListener("DOMContentLoaded", async () => {
    const sidebarContainer = document.getElementById("sidebarContainer");
    if (sidebarContainer) {
      try {
        const res = await fetch("sidebar.html");
        const html = await res.text();
        sidebarContainer.innerHTML = html;
  
        await loadSidebarProfile(); // Populate profile info
        setupProfileModal();        // Enable profile popup
      } catch (err) {
        console.error("Failed to load sidebar:", err);
      }
    }
  });
  
  async function loadSidebarProfile() {
    const currentUser = localStorage.getItem("username");
    if (!currentUser) return;
  
    try {
      const res = await fetch(`http://localhost:5000/profile?username=${currentUser}`);
      const data = await res.json();
      if (data.success) {
        document.getElementById("profileUsername").textContent = data.profile.username;
        document.getElementById("profileRole").textContent = data.profile.role;
        document.getElementById("profileAvatar").textContent = data.profile.username.charAt(0).toUpperCase();
      }
    } catch (err) {
      console.error("Failed to load profile:", err);
    }
  
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => {
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = "login.html";
      });
    }
  }
  
  function setupProfileModal() {
    const profileModal = document.getElementById("profileModal");
    const closeProfileModalBtn = document.getElementById("closeProfileModal");
    const profileAvatarEl = document.getElementById("profileAvatar");
  
    if (profileAvatarEl) {
      profileAvatarEl.addEventListener("click", async () => {
        const currentUser = localStorage.getItem("username");
        if (!currentUser) return;
  
        try {
          const res = await fetch(`http://localhost:5000/profile?username=${currentUser}`);
          const data = await res.json();
  
          if (data.success) {
            document.getElementById("modalUsername").textContent = data.profile.username;
            document.getElementById("modalRole").textContent = data.profile.role;
            profileModal.classList.add("show");
          } else {
            console.error("Profile fetch failed:", data.message);
          }
        } catch (error) {
          console.error("Failed to fetch profile:", error);
        }
      });
    }
  
    if (closeProfileModalBtn) {
      closeProfileModalBtn.addEventListener("click", () => {
        profileModal.style.display = "none";
      });
    }
  
    window.addEventListener("click", (e) => {
      if (e.target === profileModal) {
        profileModal.style.display = "none";
      }
    });
  }
  