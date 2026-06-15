function formatEta(seconds) {
  if (seconds == null || seconds < 0) return "";
  if (seconds === 0) return "· Casi listo";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m > 0) return `· ~${m} min ${s} s restantes`;
  return `· ~${s} s restantes`;
}

function statusSummary(data) {
  if (data.running) {
    const pct = data.progress ?? 0;
    return `${data.jobTypeLabel || "Trabajo"} · ${pct}%`;
  }
  if (data.status === "error") return "Error";
  if (data.status === "done") return "Completado";
  return data.statusLabel || data.status || "Listo";
}

function updateJobUI(data) {
  const logEl = document.getElementById("jobLog");
  const statusEl = document.getElementById("jobStatusLabel");
  const liveWrap = document.getElementById("jobLiveStatus");
  const typeBadge = document.getElementById("jobTypeBadge");
  const msgEl = document.getElementById("jobProgressMessage");
  const fillEl = document.getElementById("jobProgressFill");
  const pctEl = document.getElementById("jobProgressPct");
  const etaEl = document.getElementById("jobEta");
  const productsEl = document.getElementById("jobProductsLine");
  const errorEl = document.getElementById("jobErrorLine");

  if (logEl && data.log != null) {
    logEl.textContent = data.log || "Sin actividad.";
    logEl.scrollTop = logEl.scrollHeight;
  }

  if (statusEl) {
    statusEl.textContent = statusSummary(data);
  }

  if (errorEl) {
    if (data.status === "error" && data.error) {
      errorEl.hidden = false;
      errorEl.textContent = data.error;
    } else {
      errorEl.hidden = true;
      errorEl.textContent = "";
    }
  }

  if (!liveWrap) return;

  if (data.running || (data.progress > 0 && data.status !== "idle")) {
    liveWrap.hidden = false;
    const pct = Math.max(0, Math.min(100, data.progress ?? 0));
    if (typeBadge) {
      typeBadge.textContent = data.jobTypeLabel || "Trabajo";
      typeBadge.className =
        "job-type-badge " + (data.jobType === "export" ? "export" : "scrape");
    }
    if (msgEl) {
      msgEl.textContent =
        data.progressMessage ||
        (data.running ? "En curso…" : data.statusLabel || "");
    }
    if (fillEl) fillEl.style.width = pct + "%";
    if (pctEl) pctEl.textContent = pct + "% completado";
    if (etaEl) etaEl.textContent = data.running ? formatEta(data.etaSeconds) : "";

    const meta = data.progressMeta || {};
    if (productsEl) {
      if (meta.phase === "products" && meta.productsTotal) {
        productsEl.textContent = `· Producto ${meta.productsDone ?? 0}/${meta.productsTotal}`;
      } else if (meta.currentSite && meta.totalSites > 1) {
        productsEl.textContent = `· Proveedor ${meta.siteIndex ?? "?"}/${meta.totalSites}: ${meta.currentSite}`;
      } else if (meta.currentSite) {
        productsEl.textContent = `· ${meta.currentSite}`;
      } else {
        productsEl.textContent = "";
      }
    }
  } else if (data.status === "done") {
    liveWrap.hidden = false;
    if (fillEl) fillEl.style.width = "100%";
    if (pctEl) pctEl.textContent = "100% completado";
    if (msgEl) msgEl.textContent = data.progressMessage || "Completado";
    if (etaEl) etaEl.textContent = "";
    if (productsEl) productsEl.textContent = "";
  } else {
    liveWrap.hidden = true;
  }
}

async function pollJob() {
  const logEl = document.getElementById("jobLog");
  if (!logEl) return;

  let delay = 3000;
  try {
    const res = await fetch("/legacy/api/estado/");
    const data = await res.json();
    updateJobUI(data);
    delay = data.running ? 1000 : 3000;
  } catch (_) {
    delay = 5000;
  }
  setTimeout(pollJob, delay);
}

if (document.getElementById("jobLog")) {
  pollJob();
}
