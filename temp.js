
    let currentBlob = null;
    let currentFilename = "ticket.png";

    // ── API base URL: always points to Flask on port 5000 ──────
    const API = "http://127.0.0.1:5000";

    // ── Random helpers ─────────────────────────────────────────
    function randomize() {
      // Fully client-side: 18-digit ticket number
      document.getElementById("ticket_number").value =
        Array.from({length: 18}, () => Math.floor(Math.random() * 10)).join("");
      randomizeTx();
      flashInput("ticket_number");
      flashInput("transaction_id");
    }

    function randomizeTx() {
      const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
      document.getElementById("transaction_id").value =
        Array.from({length:10}, () => chars[Math.floor(Math.random()*chars.length)]).join("");
      flashInput("transaction_id");
    }

    function flashInput(id) {
      const el = document.getElementById(id);
      el.style.borderColor = "var(--accent3)";
      el.style.boxShadow = "0 0 0 3px rgba(52,211,153,0.2)";
      setTimeout(() => { el.style.borderColor = ""; el.style.boxShadow = ""; }, 800);
    }

    // ── Status helpers ─────────────────────────────────────────
    function setStatus(type, text) {
      const dot  = document.getElementById("status-dot");
      const span = document.getElementById("status-text");
      dot.className = "status-dot " + type;
      span.textContent = text;
    }

    // ── Toast ──────────────────────────────────────────────────
    let toastTimer;
    function showToast(msg, type = "success") {
      const t = document.getElementById("toast");
      const i = document.getElementById("toast-icon");
      const m = document.getElementById("toast-msg");
      i.textContent = type === "success" ? "✅" : "❌";
      m.textContent = msg;
      t.className = "toast " + type + " show";
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => { t.className = "toast"; }, 3500);
    }

    // ── Generate ───────────────────────────────────────────────
    async function generateTicket() {
      const btn    = document.getElementById("gen-btn");
      const spinner = document.getElementById("spinner");
      const empty  = document.getElementById("preview-empty");
      const img    = document.getElementById("preview-img");
      const dlSec  = document.getElementById("download-section");

      // Collect form data
      const payload = {
        company_name:   v("company_name"),
        phone:          v("phone"),
        customer:       v("customer"),
        from_location:  v("from_location"),
        to_location:    v("to_location"),
        dep_date:       v("dep_date"),
        dep_time:       v("dep_time"),
        boarding_time:  v("boarding_time"),
        ticket_number:  v("ticket_number"),
        seat_no:        v("seat_no"),
        plate_no:       v("plate_no"),
        price:          v("price"),
        cashier:        v("cashier"),
        transaction_id: v("transaction_id"),
      };

      // Basic validation
      if (!payload.customer || !payload.from_location || !payload.to_location) {
        showToast("Please fill in customer, From and To fields.", "error");
        return;
      }

      // Show loading state
      btn.disabled = true;
      btn.innerHTML = `<div class="spin-ring" style="width:18px;height:18px;border-width:2px;margin:0;"></div> Generating…`;
      empty.style.display = "none";
      img.style.display   = "none";
      dlSec.style.display = "none";
      spinner.classList.add("active");
      setStatus("idle", "Generating ticket…");

      try {
        currentFilename = `ticket_${payload.ticket_number || "new"}.png`;

        const res = await fetch(`${API}/generate`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify(payload),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ error: "Unknown error" }));
          throw new Error(err.error || `HTTP ${res.status}`);
        }

        // Blob → object URL → preview
        currentBlob = await res.blob();
        const url   = URL.createObjectURL(currentBlob);
        img.src     = url;
        img.style.display = "block";
        dlSec.style.display = "flex";

        setStatus("ready", "Ticket ready — " + new Date().toLocaleTimeString());
        showToast("Ticket generated successfully!", "success");

      } catch(e) {
        empty.style.display = "flex";
        setStatus("error", "Error: " + e.message);
        showToast("Generation failed: " + e.message, "error");

      } finally {
        spinner.classList.remove("active");
        btn.disabled = false;
        btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg> Generate Ticket`;
      }
    }

    // ── Print ──────────────────────────────────────────────────
    function printTicket() {
      if (!currentBlob) return;
      const url = URL.createObjectURL(currentBlob);
      const win = window.open("", "_blank");
      win.document.write(`
        <html>
          <head>
            <title>Print Ticket</title>
            <style>
              body { margin: 0; display: flex; justify-content: center; align-items: flex-start; padding-top: 10px; }
              img { max-width: 100%; height: auto; }
              @page { margin: 0; }
            </style>
          </head>
          <body>
            <img src="${url}" onload="window.print(); window.close();">
          </body>
        </html>
      `);
      win.document.close();
    }

    // ── Download ───────────────────────────────────────────────
    function downloadTicket() {
      if (!currentBlob) return;
      const a = document.createElement("a");
      a.href = URL.createObjectURL(currentBlob);
      a.download = currentFilename;
      a.click();
    }

    // ── Helper: get input value ────────────────────────────────
    function v(id) {
      return document.getElementById(id)?.value?.trim() ?? "";
    }

    // ── Auto-set today's date if blank ─────────────────────────
    window.addEventListener("DOMContentLoaded", () => {
      const d = document.getElementById("dep_date");
      if (!d.value) d.value = new Date().toISOString().slice(0, 10);
    });

    // ── Enter key submits ──────────────────────────────────────
    document.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.ctrlKey) generateTicket();
    });
  