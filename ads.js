// No Google request until both page content and verified CMP consent are ready.
(() => {
  const slot = document.querySelector('.ad-slot, .ranking-ad');
  if (!slot) return;
  let eligible = false, consent = false, requested = false, config;
  let scriptPromise;
  const game = document.getElementById('game');
  let reservedGameHeight = 0;
  function reserveGame() {
    if (!game || !requested) return;
    reservedGameHeight = Math.max(reservedGameHeight, game.getBoundingClientRect().height);
    game.style.minHeight = `${reservedGameHeight}px`;
  }
  if (game) new ResizeObserver(reserveGame).observe(game);
  function collapseSafely() {
    const rect = slot.getBoundingClientRect();
    // Collapsing above/inside the viewport could move a link under the pointer.
    if (rect.top >= innerHeight || rect.bottom <= 0 && scrollY === 0) slot.hidden = true;
  }
  function suppress() {
    slot.dataset.suppressed = '';
    collapseSafely();
  }
  function loadGoogle() {
    if (!scriptPromise) scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.async = true;
      script.crossOrigin = 'anonymous';
      script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6239237268971394';
      script.onload = resolve; script.onerror = reject;
      document.head.append(script);
    });
    return scriptPromise;
  }
  async function update() {
    if (!eligible || !consent || !config?.adsEnabled || document.querySelector('dialog[open]')) { suppress(); return; }
    if (slot.dataset.unfilled !== undefined) return;
    slot.hidden = false;
    delete slot.dataset.suppressed;
    if (requested) return;
    requested = true; // Never refresh the unit on guesses, mode changes or timers.
    reserveGame(); // An ad must not rise into former Top 10 controls after switching modes.
    try {
      await loadGoogle();
      if (!eligible || !consent) { suppress(); return; }
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch { suppress(); }
  }
  window.golguessAds = {setEligible(value) { eligible = !!value; update(); }};
  document.querySelectorAll('dialog').forEach(dialog => {
    new MutationObserver(update).observe(dialog, {attributes:true, attributeFilter:['open']});
  });
  new MutationObserver(() => {
    if (slot.querySelector('ins').dataset.adStatus === 'unfilled') {
      slot.dataset.unfilled = ''; suppress();
    }
  }).observe(slot.querySelector('ins'), {attributes:true, attributeFilter:['data-ad-status']});
  window.addEventListener('scroll', () => {
    if (slot.dataset.suppressed !== undefined) collapseSafely();
  }, {passive:true});
  async function connectConsent() {
    try {
      const response = await fetch('/api/public_config', {cache:'no-store'});
      if (!response.ok) return;
      config = await response.json();
      if (!config.adsEnabled || !config.cmpId) return;
      // Production host allowlist prevents preview/local ad impressions.
      if (!['golguess.com.br','www.golguess.com.br'].includes(location.hostname)) return;
      const timer = setInterval(() => {
        if (typeof window.__tcfapi !== 'function') return;
        clearInterval(timer);
        window.__tcfapi('addEventListener', 2, (tc, success) => {
          // Conservative all-region gate. gdprApplies=false is NOT consent.
          consent = !!(success && tc?.cmpStatus === 'loaded' &&
            ['tcloaded','useractioncomplete'].includes(tc.eventStatus) &&
            String(tc.cmpId) === String(config.cmpId) && tc.tcString &&
            tc.vendor?.consents?.[755] && [1,3,4].every(id => tc.purpose?.consents?.[id]));
          update();
        });
      }, 500);
      setTimeout(() => clearInterval(timer), 30000);
    } catch { suppress(); }
  }
  connectConsent();
})();
