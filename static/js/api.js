// API Client & Utility Helpers for KasPintar AI

const API = {
  getToken() {
    return localStorage.getItem("kaspintar_token");
  },

  setToken(token) {
    localStorage.setItem("kaspintar_token", token);
  },

  getUser() {
    try {
      const u = localStorage.getItem("kaspintar_user");
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("kaspintar_user", JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem("kaspintar_token");
    localStorage.removeItem("kaspintar_user");
  },

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = options.headers || {};

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // Do not set Content-Type if body is FormData
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const res = await fetch(endpoint, {
        ...options,
        headers
      });

      if (res.status === 401) {
        this.clearAuth();
        window.dispatchEvent(new CustomEvent("auth:unauthorized"));
        throw new Error("Sesi login berakhir. Silakan login kembali.");
      }

      // Check if binary download
      const contentType = res.headers.get("content-type");
      if (contentType && (contentType.includes("spreadsheetml") || contentType.includes("csv") || contentType.includes("octet-stream"))) {
        return res;
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Terjadi kesalahan pada server.");
      }
      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  },

  post(endpoint, data) {
    const isFormData = data instanceof FormData;
    return this.request(endpoint, {
      method: "POST",
      body: isFormData ? data : JSON.stringify(data)
    });
  },

  put(endpoint, data) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(data)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }
};

// Indonesian Currency & Date Formatters
function formatRupiah(number) {
  if (number === undefined || number === null || isNaN(number)) return "Rp 0";
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(number);
}

function formatDateIndo(dateStr) {
  if (!dateStr) return "-";
  try {
    const parts = dateStr.split("-");
    if (parts.length === 3) {
      const d = new Date(parts[0], parts[1] - 1, parts[2]);
      return d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
    }
    return dateStr;
  } catch {
    return dateStr;
  }
}

// Global Toast Notification
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast-msg p-4 rounded-xl shadow-lg flex items-center gap-3 text-sm font-medium ${
    type === "success" ? "bg-emerald-600 text-white" :
    type === "error" ? "bg-red-600 text-white" :
    type === "info" ? "bg-blue-600 text-white" : "bg-amber-600 text-white"
  }`;

  const iconName = type === "success" ? "check-circle" : type === "error" ? "alert-circle" : "info";
  toast.innerHTML = `
    <i data-lucide="${iconName}" class="w-5 h-5 flex-shrink-0"></i>
    <span class="flex-1">${message}</span>
    <button onclick="this.parentElement.remove()" class="text-white/80 hover:text-white">&times;</button>
  `;

  container.appendChild(toast);
  if (window.lucide) lucide.createIcons({ root: toast });

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
