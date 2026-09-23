// Refresh server-owned dates after midnight and after a suspended tab resumes.
(() => {
  let pending = false, nextAt = 0, offset = 0;
  async function refresh() {
    if (pending || document.hidden) return;
    pending = true;
    try {
      const response = await fetch('/api/daily', {cache: 'no-store'});
      if (!response.ok) return;
      const daily = await response.json();
      nextAt = Date.parse(daily.nextAt);
      offset = Date.parse(daily.serverTime) - Date.now();
      if (daily.day !== document.body.dataset.roundDay) {
        const retrospective = document.getElementById('retrospective');
        if (!retrospective) { location.reload(); return; } // Archive has no ads.
        retrospective.innerHTML = daily.retrospective; // Escaped, same-origin server template.
        document.body.dataset.roundDay = daily.day;
        document.querySelector('.round-date').textContent = `${daily.dateLabel} · Horário de Brasília`;
        document.getElementById('dayNumber').textContent = '#' + String(daily.number).padStart(3, '0');
        window.dispatchEvent(new Event('dailychange'));
      }
    } catch { /* Keep readable content; retry when connection returns. */ }
    finally { pending = false; }
  }
  setInterval(() => { if (!nextAt || Date.now() + offset >= nextAt) refresh(); }, 1000);
  document.addEventListener('visibilitychange', refresh);
  window.addEventListener('pageshow', refresh);
  window.addEventListener('online', refresh);
})();
