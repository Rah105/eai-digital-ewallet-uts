function renderDashboardCharts(transactions, users) {
  // Transaction type doughnut
  const credit = transactions.filter((t) => t.type === "credit").length;
  const debit = transactions.filter((t) => t.type === "debit").length;
  const txCtx = document.getElementById("transactionChart");
  if (txCtx) {
    new Chart(txCtx, {
      type: "doughnut",
      data: {
        labels: ["Credit", "Debit"],
        datasets: [
          { data: [credit, debit], backgroundColor: ["#198754", "#dc3545"] },
        ],
      },
      options: {
        plugins: {
          title: { display: true, text: "Transactions (Credit vs Debit)" },
        },
      },
    });
  }

  // User balances bar
  const balCtx = document.getElementById("balanceChart");
  if (balCtx && users && users.length) {
    const labels = users.map((u) => u.full_name);
    const data = users.map((u) => u.balance || 0);
    new Chart(balCtx, {
      type: "bar",
      data: { labels, datasets: [{ label: "Balance", data }] },
      options: {
        plugins: { title: { display: true, text: "User Balances" } },
        scales: { y: { beginAtZero: true } },
      },
    });
  }
}