// Financial Chart.js Handler for KasPintar AI

let trendChartInstance = null;
let categoryChartInstance = null;

const Charts = {
  renderTrendChart(canvasId, dailyTrends) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (trendChartInstance) {
      trendChartInstance.destroy();
    }

    // Default empty state
    if (!dailyTrends || dailyTrends.length === 0) {
      dailyTrends = [
        { date: "Hari 1", income: 0, expense: 0 },
        { date: "Hari 2", income: 0, expense: 0 },
        { date: "Hari 3", income: 0, expense: 0 }
      ];
    }

    const labels = dailyTrends.map((d) => formatDateIndo(d.date));
    const incomeData = dailyTrends.map((d) => d.income);
    const expenseData = dailyTrends.map((d) => d.expense);

    trendChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Pemasukan (Rp)",
            data: incomeData,
            backgroundColor: "rgba(16, 185, 129, 0.8)",
            borderColor: "#10B981",
            borderRadius: 6,
            borderWidth: 1
          },
          {
            label: "Pengeluaran (Rp)",
            data: expenseData,
            backgroundColor: "rgba(239, 68, 68, 0.8)",
            borderColor: "#EF4444",
            borderRadius: 6,
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: { boxWidth: 12, font: { family: "inherit", weight: "bold" } }
          },
          tooltip: {
            callbacks: {
              label: (context) => `${context.dataset.label}: ${formatRupiah(context.raw)}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => {
                if (value >= 1000000) return (value / 1000000).toFixed(1) + " Jt";
                if (value >= 1000) return (value / 1000).toFixed(0) + " Rb";
                return value;
              }
            }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  },

  renderCategoryChart(canvasId, expenseByCat) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (categoryChartInstance) {
      categoryChartInstance.destroy();
    }

    const keys = Object.keys(expenseByCat || {});
    const values = Object.values(expenseByCat || {});

    if (keys.length === 0) {
      // Empty placeholder
      categoryChartInstance = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: ["Belum Ada Pengeluaran"],
          datasets: [{ data: [1], backgroundColor: ["#E2E8F0"] }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            tooltip: { enabled: false },
            legend: { position: "bottom" }
          },
          cutout: "70%"
        }
      });
      return;
    }

    const palette = [
      "#EF4444", "#F97316", "#F59E0B", "#10B981", "#06B6D4",
      "#3B82F6", "#6366F1", "#8B5CF6", "#EC4899", "#64748B"
    ];

    categoryChartInstance = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: keys,
        datasets: [{
          data: values,
          backgroundColor: palette.slice(0, keys.length),
          borderWidth: 2,
          borderColor: "#FFFFFF"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 10, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const total = values.reduce((a, b) => a + b, 0);
                const pct = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                return ` ${context.label}: ${formatRupiah(context.raw)} (${pct}%)`;
              }
            }
          }
        },
        cutout: "68%"
      }
    });
  }
};
