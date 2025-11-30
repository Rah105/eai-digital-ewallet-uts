function openTopupModal() {
  new bootstrap.Modal(document.getElementById("topupModal")).show();
}

function openTransactionModal() {
  new bootstrap.Modal(document.getElementById("transactionModal")).show();
}

function showToast(message, isSuccess = true) {
  const toastEl = document.getElementById("liveToast");
  const toastMsg = document.getElementById("toast-message");
  toastMsg.textContent = message;
  toastEl.classList.toggle("text-bg-success", isSuccess);
  toastEl.classList.toggle("text-bg-danger", !isSuccess);
  const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
  toast.show();
}

async function submitTopup(e) {
  e.preventDefault();
  const amount = e.target.amount.value;

  const res = await fetch("/topup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount }),
  });
  const data = await res.json();
  bootstrap.Modal.getInstance(document.getElementById("topupModal")).hide();

  if (res.ok && data.ok) {
    document.getElementById("balance-text").textContent = `Rp ${Number(
      data.balance
    ).toLocaleString("id-ID")}`;
    showToast(`✅ ${data.message}`, true);
  } else {
    showToast(`❌ ${data.error}`, false);
  }
}

async function submitTransaction(e) {
  e.preventDefault();
  const form = e.target;
  const type = form.type.value;
  const amount = form.amount.value;

  const res = await fetch("/transactions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, amount }),
  });
  const data = await res.json();
  bootstrap.Modal.getInstance(
    document.getElementById("transactionModal")
  ).hide();

  if (res.ok && data.ok) {
    if (data.balance !== undefined) {
      document.getElementById("balance-text").textContent = `Rp ${Number(
        data.balance
      ).toLocaleString("id-ID")}`;
    }
    if (Array.isArray(data.transactions)) {
      const tbody = document.getElementById("transaction-table-body");
      tbody.innerHTML = "";
      data.transactions.forEach((t) => {
        tbody.innerHTML += `
          <tr>
            <td>${t.id}</td>
            <td>${t.type.charAt(0).toUpperCase() + t.type.slice(1)}</td>
            <td>Rp ${Number(t.amount).toLocaleString("id-ID")}</td>
            <td>${t.created_at || "—"}</td>
          </tr>`;
      });
    }
    showToast(`✅ ${data.message || "Transaction successful!"}`, true);
  } else {
    showToast(`❌ ${data.error || "Failed to create transaction."}`, false);
  }
}

function requestReport() {
  fetch("/request-report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
    .then((r) => r.json())
    .then((d) => showToast(d.ok ? `✅ ${d.message}` : `❌ ${d.error}`, d.ok))
    .catch(() => showToast("❌ Failed to send report request.", false));
}
