// Authentication Handler for KasPintar AI

const Auth = {
  currentUser: null,

  init() {
    this.currentUser = API.getUser();
    this.setupEventListeners();
    this.updateUI();

    window.addEventListener("auth:unauthorized", () => {
      this.logout(false);
      showToast("Sesi Anda berakhir. Silakan login kembali.", "info");
    });
  },

  setupEventListeners() {
    // Login form submit
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;
        const btn = document.getElementById("login-submit-btn");

        try {
          btn.disabled = true;
          btn.innerHTML = `<span class="inline-block animate-spin mr-2">⏳</span> Masuk...`;
          const res = await API.post("/api/auth/login", { email, password });
          API.setToken(res.access_token);
          API.setUser(res.user);
          this.currentUser = res.user;

          showToast(`Selamat datang kembali, ${res.user.name}!`, "success");
          this.updateUI();
          if (window.App) App.loadInitialData();
        } catch (err) {
          showToast(err.message, "error");
        } finally {
          btn.disabled = false;
          btn.innerHTML = `Masuk ke Aplikasi`;
        }
      });
    }

    // Register form submit
    const registerForm = document.getElementById("register-form");
    if (registerForm) {
      registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("register-name").value;
        const email = document.getElementById("register-email").value;
        const password = document.getElementById("register-password").value;
        const btn = document.getElementById("register-submit-btn");

        try {
          btn.disabled = true;
          btn.innerHTML = `<span class="inline-block animate-spin mr-2">⏳</span> Mendaftar...`;
          const res = await API.post("/api/auth/register", { name, email, password });
          API.setToken(res.access_token);
          API.setUser(res.user);
          this.currentUser = res.user;

          showToast(`Akun berhasil dibuat! Peran Anda: ${res.user.role}`, "success");
          this.updateUI();
          if (window.App) App.loadInitialData();
        } catch (err) {
          showToast(err.message, "error");
        } finally {
          btn.disabled = false;
          btn.innerHTML = `Daftar Akun Baru`;
        }
      });
    }

    // Toggle between login and register views
    const showRegisterBtn = document.getElementById("show-register-btn");
    const showLoginBtn = document.getElementById("show-login-btn");
    if (showRegisterBtn) {
      showRegisterBtn.addEventListener("click", () => {
        document.getElementById("login-box").classList.add("hidden");
        document.getElementById("register-box").classList.remove("hidden");
      });
    }
    if (showLoginBtn) {
      showLoginBtn.addEventListener("click", () => {
        document.getElementById("register-box").classList.add("hidden");
        document.getElementById("login-box").classList.remove("hidden");
      });
    }

    // Logout buttons (desktop sidebar and mobile header)
    document.querySelectorAll(".logout-btn").forEach((btn) => {
      btn.addEventListener("click", () => this.logout(true));
    });
  },

  updateUI() {
    const authContainer = document.getElementById("auth-container");
    const appContainer = document.getElementById("app-container");
    const adminNavLinks = document.querySelectorAll(".admin-only");

    if (this.currentUser && API.getToken()) {
      authContainer.classList.add("hidden");
      appContainer.classList.remove("hidden");

      // Update user info badges
      document.querySelectorAll(".user-name-display").forEach((el) => {
        el.textContent = this.currentUser.name;
      });
      document.querySelectorAll(".user-email-display").forEach((el) => {
        el.textContent = this.currentUser.email;
      });
      document.querySelectorAll(".user-role-badge").forEach((el) => {
        el.textContent = this.currentUser.role;
        el.className = `user-role-badge text-xs px-2 py-0.5 rounded-full font-semibold uppercase ${
          this.currentUser.role === "ADMIN" ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"
        }`;
      });

      // Show or hide admin links
      adminNavLinks.forEach((el) => {
        if (this.currentUser.role === "ADMIN") {
          el.classList.remove("hidden");
        } else {
          el.classList.add("hidden");
        }
      });
    } else {
      authContainer.classList.remove("hidden");
      appContainer.classList.add("hidden");
    }

    if (window.lucide) lucide.createIcons();
  },

  logout(showNotice = true) {
    API.clearAuth();
    this.currentUser = null;
    this.updateUI();
    if (showNotice) showToast("Anda telah keluar.", "info");
  }
};
