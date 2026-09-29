// Main Application Logic for KasPintar AI

const App = {
  currentView: "dashboard",
  wallets: [],
  categories: { all: [], income: [], expense: [] },
  transactions: [],
  selectedImportItems: [],
  chatHistory: [],
  pwaPromptEvent: null,

  init() {
    this.setupNavigation();
    this.setupPWA();
    this.setupModals();
    this.setupExcelImportUI();
    this.setupAIChatUI();
    this.setupAdminUI();

    if (Auth.currentUser) {
      this.loadInitialData();
    }
  },

  setupPWA() {
    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      this.pwaPromptEvent = e;
      const banner = document.getElementById("pwa-install-banner");
      if (banner) banner.classList.remove("hidden");
    });

    const installBtn = document.getElementById("pwa-install-btn");
    if (installBtn) {
      installBtn.addEventListener("click", async () => {
        if (!this.pwaPromptEvent) return;
        this.pwaPromptEvent.prompt();
        const choice = await this.pwaPromptEvent.userChoice;
        if (choice.outcome === "accepted") {
          showToast("Aplikasi KasPintar AI berhasil dipasang di perangkat!", "success");
        }
        this.pwaPromptEvent = null;
        document.getElementById("pwa-install-banner")?.classList.add("hidden");
      });
    }

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch((err) => {
        console.warn("ServiceWorker registration failed:", err);
      });
    }
  },

  setupNavigation() {
    // Desktop & Mobile Navigation Links
    document.querySelectorAll("[data-nav]").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        const targetView = el.getAttribute("data-nav");
        this.switchView(targetView);
      });
    });
  },

  switchView(viewName) {
    this.currentView = viewName;

    // Toggle active classes on nav links
    document.querySelectorAll("[data-nav]").forEach((el) => {
      const active = el.getAttribute("data-nav") === viewName;
      if (el.classList.contains("mobile-nav-item")) {
        el.classList.toggle("text-emerald-600", active);
        el.classList.toggle("text-slate-400", !active);
      } else {
        el.classList.toggle("bg-emerald-50", active);
        el.classList.toggle("text-emerald-700", active);
        el.classList.toggle("font-semibold", active);
        el.classList.toggle("text-slate-600", !active);
      }
    });

    // Toggle view containers
    document.querySelectorAll(".view-section").forEach((sec) => {
      sec.classList.add("hidden");
    });
    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) {
      targetSection.classList.remove("hidden");
    }

    // Refresh view data
    if (viewName === "dashboard") {
      this.loadDashboardData();
    } else if (viewName === "transactions") {
      this.loadTransactions();
    } else if (viewName === "ai-analytics") {
      this.loadAIAnalytics();
    } else if (viewName === "wallets") {
      this.loadWallets();
    } else if (viewName === "admin") {
      this.loadAdminData();
    }

    if (window.lucide) lucide.createIcons();
    window.scrollTo({ top: 0, behavior: "smooth" });
  },

  async loadInitialData() {
    try {
      await Promise.all([this.loadWallets(), this.loadCategories()]);
      this.switchView("dashboard");
    } catch (err) {
      console.error("Initial data load error:", err);
    }
  },

  async loadWallets() {
    try {
      const res = await API.get("/api/wallets");
      this.wallets = res.wallets || [];
      this.renderWallets(this.wallets, res.total_balance || 0);
      this.populateWalletSelects();
    } catch (err) {
      showToast("Gagal memuat akun kas: " + err.message, "error");
    }
  },

  populateWalletSelects() {
    const selects = ["txn-wallet-select", "txn-transfer-target", "filter-wallet-select", "import-target-wallet"];
    selects.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      const currentVal = el.value;
      const isFilter = id === "filter-wallet-select";

      el.innerHTML = isFilter ? `<option value="">Semua Akun Kas</option>` : "";
      this.wallets.forEach((w) => {
        el.innerHTML += `<option value="${w.id}">${w.name} (${formatRupiah(w.current_balance)})</option>`;
      });
      if (currentVal) el.value = currentVal;
    });
  },

  async loadCategories() {
    try {
      const res = await API.get("/api/categories");
      this.categories.all = res.categories || [];
      this.categories.income = res.income || [];
      this.categories.expense = res.expense || [];
      this.populateCategorySelects();
    } catch (err) {
      console.warn("Failed to load categories:", err);
    }
  },

  populateCategorySelects(txnType = "EXPENSE") {
    const el = document.getElementById("txn-category-select");
    const filterEl = document.getElementById("filter-category-select");

    if (filterEl) {
      const cur = filterEl.value;
      filterEl.innerHTML = `<option value="">Semua Kategori</option>`;
      this.categories.all.forEach((c) => {
        filterEl.innerHTML += `<option value="${c.id}">${c.name} (${c.type === "INCOME" ? "Masuk" : "Keluar"})</option>`;
      });
      if (cur) filterEl.value = cur;
    }

    if (el) {
      const list = txnType === "INCOME" ? this.categories.income : this.categories.expense;
      el.innerHTML = `<option value="">Pilih Kategori</option>`;
      list.forEach((c) => {
        el.innerHTML += `<option value="${c.id}">${c.name}</option>`;
      });
    }
  },

  async loadDashboardData() {
    try {
      const summary = await API.get("/api/transactions/summary");
      document.getElementById("dash-total-balance").textContent = formatRupiah(summary.total_balance);
      document.getElementById("dash-total-income").textContent = formatRupiah(summary.total_income);
      document.getElementById("dash-total-expense").textContent = formatRupiah(summary.total_expense);

      const netEl = document.getElementById("dash-net-cashflow");
      netEl.textContent = formatRupiah(summary.net_cashflow);
      netEl.className = `text-2xl font-bold ${summary.net_cashflow >= 0 ? "text-emerald-600" : "text-red-600"}`;

      // Render Charts
      Charts.renderTrendChart("chart-cashflow-trends", summary.daily_trends);
      Charts.renderCategoryChart("chart-expense-categories", summary.expense_by_category);

      // Load Recent Transactions
      const txnsRes = await API.get("/api/transactions?limit=6");
      this.renderRecentTransactions(txnsRes.items || []);
    } catch (err) {
      console.error("Dashboard error:", err);
    }
  },

  renderRecentTransactions(items) {
    const container = document.getElementById("dash-recent-transactions");
    if (!container) return;

    if (items.length === 0) {
      container.innerHTML = `
        <div class="text-center py-8 text-slate-400">
          <i data-lucide="receipt" class="w-10 h-10 mx-auto mb-2 opacity-50"></i>
          <p class="text-sm">Belum ada transaksi dicatat.</p>
        </div>
      `;
      if (window.lucide) lucide.createIcons({ root: container });
      return;
    }

    container.innerHTML = items.map((t) => {
      const isIncome = t.type === "INCOME";
      const isTransfer = t.type === "TRANSFER";
      const badgeBg = isIncome ? "bg-emerald-100 text-emerald-800" : (isTransfer ? "bg-blue-100 text-blue-800" : "bg-red-100 text-red-800");
      const icon = isIncome ? "arrow-down-left" : (isTransfer ? "repeat" : "arrow-up-right");
      const amountPrefix = isIncome ? "+" : (isTransfer ? "⇄" : "-");

      return `
        <div class="flex items-center justify-between p-3.5 hover:bg-slate-50 rounded-xl transition border border-slate-100">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center ${badgeBg}">
              <i data-lucide="${icon}" class="w-5 h-5"></i>
            </div>
            <div>
              <p class="text-sm font-semibold text-slate-800 line-clamp-1">${t.description}</p>
              <div class="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                <span>${formatDateIndo(t.date)}</span>
                <span>•</span>
                <span>${t.wallet?.name || "Kas"}</span>
                ${t.category ? `<span>•</span><span class="text-slate-500">${t.category.name}</span>` : ""}
              </div>
            </div>
          </div>
          <div class="text-right">
            <p class="text-sm font-bold ${isIncome ? "text-emerald-600" : (isTransfer ? "text-blue-600" : "text-red-600")}">
              ${amountPrefix} ${formatRupiah(t.amount)}
            </p>
          </div>
        </div>
      `;
    }).join("");

    if (window.lucide) lucide.createIcons({ root: container });
  },

  renderWallets(wallets, totalBal) {
    const containers = [
      document.getElementById("wallets-list-container"),
      document.getElementById("wallets-grid-full")
    ].filter(Boolean);

    if (containers.length === 0) return;

    if (wallets.length === 0) {
      containers.forEach(c => c.innerHTML = `<p class="text-sm text-slate-400 py-4">Belum ada akun kas.</p>`);
      return;
    }

    const html = wallets.map((w) => {
      return `
        <div class="p-5 rounded-2xl border border-slate-100 bg-white shadow-sm hover:shadow-md transition flex flex-col justify-between" style="border-top: 4px solid ${w.color}">
          <div class="flex items-start justify-between">
            <div>
              <span class="text-xs uppercase tracking-wider font-semibold text-slate-400">${w.type}</span>
              <h3 class="text-base font-bold text-slate-800 mt-0.5">${w.name}</h3>
            </div>
            <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white" style="background-color: ${w.color}">
              <i data-lucide="${w.icon || 'wallet'}" class="w-5 h-5"></i>
            </div>
          </div>
          <div class="mt-4 pt-4 border-t border-slate-100 flex items-end justify-between">
            <div>
              <p class="text-xs text-slate-400">Saldo Kas</p>
              <p class="text-lg font-bold text-slate-900">${formatRupiah(w.current_balance)}</p>
            </div>
            <button onclick="App.deleteWallet(${w.id})" class="text-xs text-slate-400 hover:text-red-600 font-medium">Hapus</button>
          </div>
        </div>
      `;
    }).join("");

    containers.forEach(c => {
      c.innerHTML = html;
      if (window.lucide) lucide.createIcons({ root: c });
    });
  },

  async deleteWallet(id) {
    if (!confirm("Hapus akun kas ini? Data transaksi terkait akan tetap tersimpan.")) return;
    try {
      await API.delete(`/api/wallets/${id}`);
      showToast("Akun kas berhasil dihapus", "success");
      this.loadWallets();
    } catch (err) {
      showToast("Gagal menghapus kas: " + err.message, "error");
    }
  },

  async loadTransactions(page = 1) {
    const walletId = document.getElementById("filter-wallet-select")?.value || "";
    const categoryId = document.getElementById("filter-category-select")?.value || "";
    const type = document.getElementById("filter-type-select")?.value || "";
    const search = document.getElementById("filter-search-input")?.value || "";
    const startDate = document.getElementById("filter-start-date")?.value || "";
    const endDate = document.getElementById("filter-end-date")?.value || "";

    const query = new URLSearchParams({
      page,
      limit: 20,
      ...(walletId && { wallet_id: walletId }),
      ...(categoryId && { category_id: categoryId }),
      ...(type && { type: type }),
      ...(search && { search: search }),
      ...(startDate && { start_date: startDate }),
      ...(endDate && { end_date: endDate })
    });

    try {
      const res = await API.get(`/api/transactions?${query.toString()}`);
      this.transactions = res.items || [];
      this.renderTransactionTable(res);
    } catch (err) {
      showToast("Gagal memuat transaksi: " + err.message, "error");
    }
  },

  renderTransactionTable(data) {
    const tbody = document.getElementById("transactions-tbody");
    const countEl = document.getElementById("txns-total-count");
    if (countEl) countEl.textContent = `${data.total} Transaksi Ditemukan`;

    if (!tbody) return;

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-12 text-slate-400">
            <i data-lucide="inbox" class="w-10 h-10 mx-auto mb-2 opacity-40"></i>
            <p class="text-sm">Tidak ada transaksi yang cocok dengan filter.</p>
          </td>
        </tr>
      `;
      if (window.lucide) lucide.createIcons({ root: tbody });
      return;
    }

    tbody.innerHTML = data.items.map((t) => {
      const isIncome = t.type === "INCOME";
      const isTransfer = t.type === "TRANSFER";
      const badgeClass = isIncome ? "bg-emerald-50 text-emerald-700 border-emerald-200" : (isTransfer ? "bg-blue-50 text-blue-700 border-blue-200" : "bg-red-50 text-red-700 border-red-200");
      const typeLabel = isIncome ? "Pemasukan" : (isTransfer ? "Transfer" : "Pengeluaran");

      return `
        <tr class="hover:bg-slate-50 transition border-b border-slate-100">
          <td class="px-4 py-3.5 text-xs font-medium text-slate-500 whitespace-nowrap">
            ${formatDateIndo(t.date)}
          </td>
          <td class="px-4 py-3.5">
            <p class="text-sm font-semibold text-slate-800">${t.description}</p>
            ${t.note ? `<p class="text-xs text-slate-400 mt-0.5 line-clamp-1">${t.note}</p>` : ""}
          </td>
          <td class="px-4 py-3.5 whitespace-nowrap">
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${badgeClass}">
              ${typeLabel}
            </span>
          </td>
          <td class="px-4 py-3.5 text-xs text-slate-600 whitespace-nowrap">
            ${t.category?.name || "-"}
          </td>
          <td class="px-4 py-3.5 text-xs text-slate-600 whitespace-nowrap">
            <span class="font-medium">${t.wallet?.name || "Kas"}</span>
            ${t.transfer_wallet ? ` ➔ <span class="font-medium">${t.transfer_wallet.name}</span>` : ""}
          </td>
          <td class="px-4 py-3.5 text-right whitespace-nowrap">
            <span class="text-sm font-bold ${isIncome ? "text-emerald-600" : (isTransfer ? "text-blue-600" : "text-red-600")}">
              ${isIncome ? "+" : (isTransfer ? "⇄" : "-")} ${formatRupiah(t.amount)}
            </span>
          </td>
          <td class="px-4 py-3.5 text-center whitespace-nowrap">
            <div class="flex items-center justify-center gap-2">
              <button onclick="App.deleteTransaction(${t.id})" class="text-slate-400 hover:text-red-600 p-1 rounded-lg transition" title="Hapus">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join("");

    // Render Pagination Controls
    const pagContainer = document.getElementById("txns-pagination");
    if (pagContainer) {
      if (data.total_pages <= 1) {
        pagContainer.innerHTML = "";
      } else {
        pagContainer.innerHTML = `
          <div class="flex items-center gap-2 text-xs">
            <button ${data.page <= 1 ? "disabled class='opacity-50 cursor-not-allowed'" : `onclick="App.loadTransactions(${data.page - 1})"`} class="px-3 py-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium">Sebelumnya</button>
            <span class="text-slate-600">Halaman ${data.page} dari ${data.total_pages}</span>
            <button ${data.page >= data.total_pages ? "disabled class='opacity-50 cursor-not-allowed'" : `onclick="App.loadTransactions(${data.page + 1})"`} class="px-3 py-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 font-medium">Selanjutnya</button>
          </div>
        `;
      }
    }

    if (window.lucide) lucide.createIcons({ root: tbody });
  },

  async deleteTransaction(id) {
    if (!confirm("Apakah Anda yakin ingin menghapus transaksi ini?")) return;
    try {
      await API.delete(`/api/transactions/${id}`);
      showToast("Transaksi berhasil dihapus", "success");
      this.loadTransactions();
      this.loadWallets();
    } catch (err) {
      showToast("Gagal menghapus: " + err.message, "error");
    }
  },

  setupModals() {
    // Add Transaction Modal
    const modal = document.getElementById("modal-transaction");
    const openBtns = document.querySelectorAll(".open-add-txn-modal");
    const closeBtn = document.getElementById("close-txn-modal-btn");
    const form = document.getElementById("form-transaction");

    openBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        // Set default date to today
        document.getElementById("txn-date").value = new Date().toISOString().split("T")[0];
        document.getElementById("txn-type-income").checked = true;
        this.updateTxnFormType("INCOME");
        modal.classList.remove("hidden");
      });
    });

    closeBtn?.addEventListener("click", () => modal.classList.add("hidden"));

    // Handle Type radio changes (INCOME vs EXPENSE vs TRANSFER)
    document.querySelectorAll("input[name='txn_type']").forEach((radio) => {
      radio.addEventListener("change", (e) => {
        this.updateTxnFormType(e.target.value);
      });
    });

    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const type = document.querySelector("input[name='txn_type']:checked").value;
      const amount = parseFloat(document.getElementById("txn-amount").value);
      const date = document.getElementById("txn-date").value;
      const walletId = parseInt(document.getElementById("txn-wallet-select").value);
      const categoryId = document.getElementById("txn-category-select").value ? parseInt(document.getElementById("txn-category-select").value) : null;
      const transferWalletId = document.getElementById("txn-transfer-target").value ? parseInt(document.getElementById("txn-transfer-target").value) : null;
      const description = document.getElementById("txn-desc").value;
      const note = document.getElementById("txn-note").value;

      try {
        await API.post("/api/transactions", {
          wallet_id: walletId,
          category_id: type === "TRANSFER" ? null : categoryId,
          type,
          amount,
          date,
          description,
          note,
          transfer_wallet_id: type === "TRANSFER" ? transferWalletId : null
        });

        showToast("Transaksi berhasil disimpan!", "success");
        modal.classList.add("hidden");
        form.reset();

        this.loadWallets();
        if (this.currentView === "dashboard") this.loadDashboardData();
        if (this.currentView === "transactions") this.loadTransactions();
      } catch (err) {
        showToast(err.message, "error");
      }
    });

    // Add Wallet Modal
    const walletModal = document.getElementById("modal-wallet");
    const openWalletBtn = document.getElementById("open-add-wallet-btn");
    const closeWalletBtn = document.getElementById("close-wallet-modal-btn");
    const walletForm = document.getElementById("form-wallet");

    openWalletBtn?.addEventListener("click", () => walletModal.classList.remove("hidden"));
    closeWalletBtn?.addEventListener("click", () => walletModal.classList.add("hidden"));

    walletForm?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("wallet-name").value;
      const type = document.getElementById("wallet-type").value;
      const initial_balance = parseFloat(document.getElementById("wallet-init-bal").value || 0);
      const color = document.getElementById("wallet-color").value;

      try {
        await API.post("/api/wallets", { name, type, initial_balance, color, icon: "wallet" });
        showToast("Akun kas baru berhasil dibuat!", "success");
        walletModal.classList.add("hidden");
        walletForm.reset();
        this.loadWallets();
      } catch (err) {
        showToast(err.message, "error");
      }
    });

    // Export Buttons
    document.getElementById("btn-export-excel")?.addEventListener("click", () => {
      window.location.href = `/api/transactions/export?format=xlsx`;
    });
    document.getElementById("btn-export-csv")?.addEventListener("click", () => {
      window.location.href = `/api/transactions/export?format=csv`;
    });

    // Filter Listeners
    ["filter-wallet-select", "filter-category-select", "filter-type-select", "filter-start-date", "filter-end-date"].forEach((id) => {
      document.getElementById(id)?.addEventListener("change", () => this.loadTransactions(1));
    });
    document.getElementById("filter-search-input")?.addEventListener("input", debounce(() => this.loadTransactions(1), 400));
  },

  updateTxnFormType(type) {
    const catGroup = document.getElementById("txn-category-group");
    const transferGroup = document.getElementById("txn-transfer-group");

    if (type === "TRANSFER") {
      catGroup.classList.add("hidden");
      transferGroup.classList.remove("hidden");
    } else {
      catGroup.classList.remove("hidden");
      transferGroup.classList.add("hidden");
      this.populateCategorySelects(type);
    }
  },

  // ==========================================
  // SMART EXCEL IMPORT LOGIC
  // ==========================================
  setupExcelImportUI() {
    const dropzone = document.getElementById("excel-dropzone");
    const fileInput = document.getElementById("excel-file-input");
    const scanBtn = document.getElementById("excel-scan-btn");
    const confirmBtn = document.getElementById("btn-confirm-import");

    dropzone?.addEventListener("click", () => fileInput?.click());

    fileInput?.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        document.getElementById("excel-file-name").textContent = e.target.files[0].name;
        document.getElementById("excel-file-info").classList.remove("hidden");
      }
    });

    scanBtn?.addEventListener("click", async () => {
      const file = fileInput.files[0];
      if (!file) {
        showToast("Silakan pilih berkas Excel atau CSV terlebih dahulu.", "info");
        return;
      }

      const useAi = document.getElementById("excel-use-ai-toggle").checked;
      const formData = new FormData();
      formData.append("file", file);
      formData.append("use_ai", useAi);

      try {
        scanBtn.disabled = true;
        scanBtn.innerHTML = `<span class="inline-block animate-spin mr-2">⏳</span> Membaca & Menganalisis Berkas...`;
        
        const res = await API.post("/api/excel/parse", formData);
        if (!res.success) {
          throw new Error(res.error || "Gagal memproses berkas.");
        }

        this.selectedImportItems = res.transactions || [];
        this.renderImportPreview(res);
        showToast(`Berhasil membaca ${res.total_parsed} transaksi: ${res.income_count || 0} Pemasukan, ${res.expense_count || 0} Pengeluaran!`, "success");
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        scanBtn.disabled = false;
        scanBtn.innerHTML = `<i data-lucide="scan-line" class="w-4 h-4 mr-2"></i> Mulai Pindai Berkas`;
        if (window.lucide) lucide.createIcons();
      }
    });

    confirmBtn?.addEventListener("click", async () => {
      const walletId = parseInt(document.getElementById("import-target-wallet").value);
      if (!walletId) {
        showToast("Pilih akun kas tujuan terlebih dahulu.", "error");
        return;
      }

      // Collect checked items
      const checkedCheckboxes = document.querySelectorAll(".import-item-checkbox:checked");
      const itemsToImport = [];
      checkedCheckboxes.forEach((cb) => {
        const id = parseInt(cb.dataset.id);
        const item = this.selectedImportItems.find((x) => x.temp_id === id);
        if (item) {
          itemsToImport.push({
            date: item.date,
            description: item.description,
            type: item.type,
            amount: item.amount,
            category_name: item.category,
            note: item.note
          });
        }
      });

      if (itemsToImport.length === 0) {
        showToast("Pilih setidaknya satu baris transaksi untuk diimpor.", "info");
        return;
      }

      try {
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = `<span class="inline-block animate-spin mr-2">⏳</span> Mengimpor Transaksi...`;

        const res = await API.post("/api/excel/confirm-import", {
          wallet_id: walletId,
          transactions: itemsToImport
        });

        showToast(res.message, "success");
        // Reset preview
        document.getElementById("import-preview-container")?.classList.add("hidden");
        fileInput.value = "";
        document.getElementById("excel-file-info")?.classList.add("hidden");

        this.loadWallets();
        this.switchView("transactions");
      } catch (err) {
        showToast("Gagal mengimpor: " + err.message, "error");
      } finally {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 mr-2"></i> Simpan Transaksi ke Kas`;
        if (window.lucide) lucide.createIcons();
      }
    });

    // Check all checkbox
    document.getElementById("import-check-all")?.addEventListener("change", (e) => {
      document.querySelectorAll(".import-item-checkbox").forEach((cb) => {
        cb.checked = e.target.checked;
      });
      this.updateImportSummaryCount();
    });
  },

  importFilterMode: "ALL",

  renderImportPreview(res) {
    const container = document.getElementById("import-preview-container");
    const badge = document.getElementById("import-scan-mode-badge");

    if (badge) {
      badge.textContent = res.mode === "gemini_ai" ? "Gemini AI Deep Scan" : "Pendeteksi Otomatis Cerdas";
      badge.className = `text-xs px-2.5 py-1 rounded-full font-medium ${res.mode === "gemini_ai" ? "bg-purple-100 text-purple-800" : "bg-emerald-100 text-emerald-800"}`;
    }

    container?.classList.remove("hidden");
    this.importFilterMode = "ALL";
    this.renderImportRows();
  },

  renderImportRows() {
    const tbody = document.getElementById("import-preview-tbody");
    if (!tbody) return;

    let items = this.selectedImportItems;
    if (this.importFilterMode === "INCOME") {
      items = items.filter(t => t.type === "INCOME");
    } else if (this.importFilterMode === "EXPENSE") {
      items = items.filter(t => t.type === "EXPENSE");
    }

    if (items.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-8 text-slate-400">
            Tidak ada transaksi dalam filter ini.
          </td>
        </tr>
      `;
      this.updateImportSummaryCount();
      return;
    }

    tbody.innerHTML = items.map((t) => {
      const isIncome = t.type === "INCOME";
      return `
        <tr class="hover:bg-slate-50 transition border-b border-slate-100 text-xs">
          <td class="px-3 py-2.5 text-center">
            <input type="checkbox" data-id="${t.temp_id}" class="import-item-checkbox rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4" checked onchange="App.updateImportSummaryCount()">
          </td>
          <td class="px-3 py-2.5 whitespace-nowrap text-slate-600 font-mono">${t.date}</td>
          <td class="px-3 py-2.5 font-medium text-slate-800">${t.description}</td>
          <td class="px-3 py-2.5 whitespace-nowrap">
            <select onchange="App.changeImportItemType(${t.temp_id}, this.value)" class="text-xs font-bold py-1 px-2 rounded-lg border ${isIncome ? 'border-emerald-300 bg-emerald-50 text-emerald-800' : 'border-red-300 bg-red-50 text-red-800'}">
              <option value="INCOME" ${isIncome ? "selected" : ""}>🟢 Pemasukan (+)</option>
              <option value="EXPENSE" ${!isIncome ? "selected" : ""}>🔴 Pengeluaran (-)</option>
            </select>
          </td>
          <td class="px-3 py-2.5 whitespace-nowrap text-slate-600">${t.category}</td>
          <td class="px-3 py-2.5 text-right font-bold whitespace-nowrap ${isIncome ? "text-emerald-600" : "text-red-600"}">
            ${isIncome ? "+" : "-"} ${formatRupiah(t.amount)}
          </td>
        </tr>
      `;
    }).join("");

    this.updateImportSummaryCount();
  },

  changeImportItemType(temp_id, newType) {
    const item = this.selectedImportItems.find(x => x.temp_id === temp_id);
    if (item) {
      item.type = newType;
      this.renderImportRows();
    }
  },

  setAllImportType(newType) {
    this.selectedImportItems.forEach(t => t.type = newType);
    this.renderImportRows();
    showToast(`Semua transaksi diubah menjadi ${newType === "INCOME" ? "Pemasukan" : "Pengeluaran"}`, "info");
  },

  filterImportPreview(mode) {
    this.importFilterMode = mode;
    ["filter-imp-all", "filter-imp-in", "filter-imp-out"].forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      el.className = "px-2.5 py-1 rounded-lg font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 transition";
    });

    const activeBtn = mode === "ALL" ? document.getElementById("filter-imp-all") :
                      (mode === "INCOME" ? document.getElementById("filter-imp-in") : document.getElementById("filter-imp-out"));
    if (activeBtn) {
      activeBtn.className = "px-2.5 py-1 rounded-lg font-bold bg-emerald-600 text-white transition";
    }

    this.renderImportRows();
  },

  updateImportSummaryCount() {
    const total = this.selectedImportItems.length;
    const checked = document.querySelectorAll(".import-item-checkbox:checked").length;
    const inCount = this.selectedImportItems.filter(t => t.type === "INCOME").length;
    const outCount = this.selectedImportItems.filter(t => t.type === "EXPENSE").length;

    const countEl = document.getElementById("import-selected-count");
    if (countEl) countEl.textContent = `${checked} dari ${total} Transaksi Terpilih`;

    const inBadge = document.getElementById("import-income-count-badge");
    if (inBadge) inBadge.textContent = `+${inCount} Pemasukan`;

    const outBadge = document.getElementById("import-expense-count-badge");
    if (outBadge) outBadge.textContent = `-${outCount} Pengeluaran`;
  },

  // ==========================================
  // AI FINANCIAL ANALYTICS & CHAT
  // ==========================================
  async loadAIAnalytics() {
    const cardContainer = document.getElementById("ai-health-result");
    try {
      cardContainer.innerHTML = `
        <div class="p-8 text-center text-slate-400 animate-pulse">
          <i data-lucide="sparkles" class="w-10 h-10 mx-auto mb-3 text-purple-500 animate-spin"></i>
          <p class="font-medium text-slate-700">AI sedang mendiagnosis riwayat kas dan keuangan Anda...</p>
          <p class="text-xs text-slate-400 mt-1">Mengevaluasi arus kas, pola pengeluaran, rasio tabungan, dan proyeksi.</p>
        </div>
      `;
      if (window.lucide) lucide.createIcons({ root: cardContainer });

      const res = await API.get("/api/ai/health-check");
      const a = res.analysis;

      let scoreColor = "text-emerald-600";
      let scoreBg = "bg-emerald-50 border-emerald-200";
      if (a.score < 60) {
        scoreColor = "text-red-600";
        scoreBg = "bg-red-50 border-red-200";
      } else if (a.score < 80) {
        scoreColor = "text-amber-600";
        scoreBg = "bg-amber-50 border-amber-200";
      }

      cardContainer.innerHTML = `
        <!-- Health Score Header -->
        <div class="p-6 rounded-2xl border ${scoreBg} flex flex-col md:flex-row items-center justify-between gap-6">
          <div class="flex items-center gap-5">
            <div class="w-20 h-20 rounded-2xl bg-white shadow-sm flex flex-col items-center justify-center border border-slate-100">
              <span class="text-3xl font-extrabold ${scoreColor}">${a.score}</span>
              <span class="text-[10px] uppercase font-bold text-slate-400">Skor / 100</span>
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold text-slate-800">Kesehatan Finansial: ${a.status}</h3>
                <span class="text-xs px-2 py-0.5 bg-white rounded-md font-medium text-slate-500 border border-slate-200">
                  ${a.source === "gemini_ai" ? "Gemini AI" : "Analisis Cerdas"}
                </span>
              </div>
              <p class="text-sm text-slate-600 mt-1 max-w-xl">${a.summary_text}</p>
            </div>
          </div>
          <div class="text-right whitespace-nowrap">
            <span class="text-xs text-slate-500 font-medium">Rasio Tabungan / Surplus:</span>
            <p class="text-xl font-bold ${a.savings_rate_pct >= 0 ? 'text-emerald-600' : 'text-red-600'}">${a.savings_rate_pct}%</p>
          </div>
        </div>

        <!-- 3 Tactical Recommendations -->
        <div class="mt-6">
          <h4 class="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
            <i data-lucide="lightbulb" class="w-4 h-4 text-amber-500"></i> Rekomendasi Taktis AI
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            ${(a.recommendations || []).map((rec, i) => `
              <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3">
                <span class="w-6 h-6 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">${i + 1}</span>
                <p class="text-xs text-slate-700 leading-relaxed">${rec}</p>
              </div>
            `).join("")}
          </div>
        </div>

        <!-- Anomalies & Warning Flags -->
        ${(a.anomalies && a.anomalies.length > 0) ? `
          <div class="mt-6 p-4 rounded-xl bg-amber-50 border border-amber-200">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-800 flex items-center gap-2 mb-2">
              <i data-lucide="alert-triangle" class="w-4 h-4 text-amber-600"></i> Catatan & Deteksi Anomali
            </h4>
            <ul class="list-disc list-inside text-xs text-amber-900 space-y-1">
              ${a.anomalies.map(anom => `<li>${anom}</li>`).join("")}
            </ul>
          </div>
        ` : ""}

        <!-- Next Month Projection -->
        ${a.forecast_next_month ? `
          <div class="mt-6 p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-800 text-white flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-wider text-emerald-400 font-semibold flex items-center gap-1.5">
                <i data-lucide="trending-up" class="w-4 h-4"></i> Proyeksi Arus Kas Bulan Depan
              </p>
              <p class="text-xs text-slate-300 mt-1 max-w-lg">${a.forecast_next_month.advice || a.forecast_next_month.confidence || "Berdasarkan histori transaksi yang telah dicatat."}</p>
            </div>
            <div class="text-right">
              <p class="text-xs text-slate-400">Estimasi Saldo Akhir:</p>
              <p class="text-xl font-extrabold text-white">${formatRupiah(a.forecast_next_month.projected_balance || 0)}</p>
            </div>
          </div>
        ` : ""}
      `;

      if (window.lucide) lucide.createIcons({ root: cardContainer });
    } catch (err) {
      cardContainer.innerHTML = `
        <div class="p-6 text-center text-red-500 bg-red-50 rounded-2xl">
          <p class="font-semibold text-sm">Gagal memuat analisis keuangan: ${err.message}</p>
        </div>
      `;
    }
  },

  setupAIChatUI() {
    const chatInput = document.getElementById("ai-chat-input");
    const sendBtn = document.getElementById("ai-chat-send-btn");
    const messagesContainer = document.getElementById("ai-chat-messages");

    const sendMessage = async (text) => {
      const message = (text || chatInput.value).trim();
      if (!message) return;

      // Append user message
      messagesContainer.innerHTML += `
        <div class="flex items-start justify-end gap-2.5">
          <div class="bg-emerald-600 text-white rounded-2xl rounded-tr-none px-4 py-2.5 text-xs max-w-sm shadow-sm leading-relaxed">
            ${message}
          </div>
          <div class="w-7 h-7 rounded-full bg-emerald-700 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
            ${Auth.currentUser?.name?.charAt(0) || "U"}
          </div>
        </div>
      `;
      chatInput.value = "";
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

      // Loading bubble
      const loadingId = "chat-loading-" + Date.now();
      messagesContainer.innerHTML += `
        <div id="${loadingId}" class="flex items-start gap-2.5">
          <div class="w-7 h-7 rounded-full bg-purple-600 text-white flex items-center justify-center flex-shrink-0">
            <i data-lucide="bot" class="w-4 h-4"></i>
          </div>
          <div class="bg-slate-100 text-slate-500 rounded-2xl rounded-tl-none px-4 py-2.5 text-xs animate-pulse">
            Mengetik jawaban...
          </div>
        </div>
      `;
      if (window.lucide) lucide.createIcons({ root: messagesContainer });
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

      try {
        const res = await API.post("/api/ai/chat", {
          message,
          history: this.chatHistory
        });

        // Remove loading bubble
        document.getElementById(loadingId)?.remove();

        // Convert simple markdown to HTML (bold, lists)
        let formatted = res.reply
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
          .replace(/\*(.*?)\*/g, "<em>$1</em>")
          .replace(/\n\n/g, "<br><br>")
          .replace(/\n- /g, "<br>• ");

        messagesContainer.innerHTML += `
          <div class="flex items-start gap-2.5">
            <div class="w-7 h-7 rounded-full bg-purple-600 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
              <i data-lucide="bot" class="w-4 h-4"></i>
            </div>
            <div class="bg-white border border-slate-100 shadow-sm text-slate-800 rounded-2xl rounded-tl-none px-4 py-3 text-xs max-w-md leading-relaxed">
              ${formatted}
            </div>
          </div>
        `;

        this.chatHistory.push({ role: "user", content: message });
        this.chatHistory.push({ role: "model", content: res.reply });
      } catch (err) {
        document.getElementById(loadingId)?.remove();
        messagesContainer.innerHTML += `
          <div class="p-3 bg-red-50 text-red-600 text-xs rounded-xl">
            Gagal mendapatkan balasan AI: ${err.message}
          </div>
        `;
      }

      if (window.lucide) lucide.createIcons({ root: messagesContainer });
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    sendBtn?.addEventListener("click", () => sendMessage());
    chatInput?.addEventListener("keypress", (e) => {
      if (e.key === "Enter") sendMessage();
    });

    // Quick prompt buttons
    document.querySelectorAll(".ai-quick-prompt").forEach((btn) => {
      btn.addEventListener("click", () => {
        sendMessage(btn.textContent.trim());
      });
    });
  },

  // ==========================================
  // ADMIN PANEL LOGIC
  // ==========================================
  setupAdminUI() {
    // Save Gemini Key
    const saveKeyBtn = document.getElementById("admin-save-key-btn");
    saveKeyBtn?.addEventListener("click", async () => {
      const key = document.getElementById("admin-gemini-key").value;
      try {
        await API.post("/api/admin/config", { gemini_api_key: key });
        showToast("Google Gemini API Key berhasil disimpan!", "success");
        this.loadAdminConfig();
      } catch (err) {
        showToast("Gagal menyimpan key: " + err.message, "error");
      }
    });

    // Cloud Backup DB Download
    document.getElementById("btn-admin-backup")?.addEventListener("click", () => {
      window.location.href = `/api/admin/backup-db`;
    });

    // Cloud Restore DB
    const restoreInput = document.getElementById("admin-restore-file");
    restoreInput?.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      if (!confirm("PERINGATAN: Memulihkan database dari cadangan akan menggabungkan data. Lanjutkan?")) return;

      const fd = new FormData();
      fd.append("file", file);

      try {
        const res = await API.post("/api/admin/restore-db", fd);
        showToast(res.message, "success");
        this.loadAdminData();
      } catch (err) {
        showToast("Gagal memulihkan cadangan: " + err.message, "error");
      }
    });

    // Admin Create User Modal
    const userModal = document.getElementById("modal-admin-create-user");
    document.getElementById("open-admin-create-user-btn")?.addEventListener("click", () => userModal.classList.remove("hidden"));
    document.getElementById("close-admin-user-modal")?.addEventListener("click", () => userModal.classList.add("hidden"));

    document.getElementById("form-admin-create-user")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("admin-new-user-name").value;
      const email = document.getElementById("admin-new-user-email").value;
      const password = document.getElementById("admin-new-user-password").value;
      const role = document.getElementById("admin-new-user-role").value;

      try {
        await API.post("/api/admin/users", { name, email, password, role });
        showToast(`Pengguna baru ${name} berhasil dibuat!`, "success");
        userModal.classList.add("hidden");
        document.getElementById("form-admin-create-user").reset();
        this.loadAdminUsers();
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  },

  async loadAdminData() {
    await Promise.all([this.loadAdminStats(), this.loadAdminUsers(), this.loadAdminConfig()]);
  },

  async loadAdminStats() {
    try {
      const s = await API.get("/api/admin/system-stats");
      document.getElementById("admin-stat-users").textContent = `${s.active_users} / ${s.total_users}`;
      document.getElementById("admin-stat-wallets").textContent = s.total_wallets;
      document.getElementById("admin-stat-txns").textContent = s.total_transactions;
      document.getElementById("admin-stat-volume").textContent = formatRupiah(s.total_volume);
    } catch (err) {
      console.warn("Admin stats error:", err);
    }
  },

  async loadAdminConfig() {
    try {
      const cfg = await API.get("/api/admin/config");
      const badge = document.getElementById("admin-gemini-status-badge");
      if (badge) {
        badge.textContent = cfg.gemini_api_key_configured ? "Terkoneksi (" + cfg.gemini_api_key_preview + ")" : "Belum Dikonfigurasi";
        badge.className = `text-xs px-2.5 py-1 rounded-full font-semibold ${cfg.gemini_api_key_configured ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`;
      }
    } catch (err) {
      console.warn("Admin config error:", err);
    }
  },

  async loadAdminUsers() {
    const tbody = document.getElementById("admin-users-tbody");
    if (!tbody) return;

    try {
      const res = await API.get("/api/admin/users");
      tbody.innerHTML = res.users.map((u) => {
        const isAdmin = u.role === "ADMIN";
        return `
          <tr class="hover:bg-slate-50 transition border-b border-slate-100 text-xs">
            <td class="px-4 py-3.5 font-semibold text-slate-800">${u.name}</td>
            <td class="px-4 py-3.5 text-slate-500">${u.email}</td>
            <td class="px-4 py-3.5">
              <span class="px-2 py-0.5 rounded-full font-bold uppercase ${isAdmin ? "bg-amber-100 text-amber-800" : "bg-blue-100 text-blue-800"}">
                ${u.role}
              </span>
            </td>
            <td class="px-4 py-3.5">
              <span class="px-2 py-0.5 rounded-full font-medium ${u.is_active ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}">
                ${u.is_active ? "Aktif" : "Nonaktif"}
              </span>
            </td>
            <td class="px-4 py-3.5 text-slate-600">
              ${u.wallet_count} Kas • ${u.transaction_count} Txn
            </td>
            <td class="px-4 py-3.5 text-right whitespace-nowrap">
              <div class="flex items-center justify-end gap-2">
                <button onclick="App.toggleUserStatus(${u.id})" class="text-xs px-2 py-1 rounded border border-slate-200 hover:bg-slate-100">
                  ${u.is_active ? "Bekukan" : "Aktifkan"}
                </button>
                <button onclick="App.toggleUserRole(${u.id}, '${isAdmin ? "USER" : "ADMIN"}')" class="text-xs px-2 py-1 rounded border border-slate-200 hover:bg-slate-100">
                  Jadikan ${isAdmin ? "User" : "Admin"}
                </button>
                <button onclick="App.resetUserPassword(${u.id})" class="text-xs px-2 py-1 rounded border border-slate-200 hover:bg-slate-100 text-amber-700">
                  Reset Password
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

      if (window.lucide) lucide.createIcons({ root: tbody });
    } catch (err) {
      showToast("Gagal memuat pengguna: " + err.message, "error");
    }
  },

  async toggleUserStatus(id) {
    try {
      const res = await API.put(`/api/admin/users/${id}/toggle-status`, {});
      showToast(res.message, "success");
      this.loadAdminUsers();
      this.loadAdminStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  },

  async toggleUserRole(id, newRole) {
    try {
      const res = await API.put(`/api/admin/users/${id}/role`, { role: newRole });
      showToast(res.message, "success");
      this.loadAdminUsers();
    } catch (err) {
      showToast(err.message, "error");
    }
  },

  async resetUserPassword(id) {
    const newPwd = prompt("Masukkan kata sandi baru (minimal 6 karakter):");
    if (!newPwd) return;
    try {
      const res = await API.put(`/api/admin/users/${id}/reset-password`, { new_password: newPwd });
      showToast(res.message, "success");
    } catch (err) {
      showToast(err.message, "error");
    }
  }
};

// Simple debounce helper
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Global initialization
window.addEventListener("DOMContentLoaded", () => {
  Auth.init();
  App.init();
});
