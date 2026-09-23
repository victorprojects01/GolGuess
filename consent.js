// Google Privacy & Messaging bootstraps through the AdSense tag, with ads paused.
(() => {
  const listeners = new Set();
  let state = {allowed:false, ready:false, config:null};
  let regionalMessage = false;
  const pause = () => { (window.adsbygoogle = window.adsbygoogle || []).pauseAdRequests = 1; };
  function publish(next) {
    state = {...state, ...next};
    if (!state.allowed) pause();
    listeners.forEach(listener => listener(state));
  }
  window.golguessConsent = {
    subscribe(listener) { listeners.add(listener); listener(state); },
    pause,
  };
  document.querySelectorAll('[data-privacy-settings]').forEach(button => {
    button.addEventListener('click', () => {
      const status = document.getElementById('privacy-status');
      if (!regionalMessage || typeof window.googlefc?.showRevocationMessage !== 'function') {
        if (status) status.textContent = 'Preferências de publicidade indisponíveis no momento ou nesta região.';
        return;
      }
      publish({allowed:false});
      try { window.googlefc.showRevocationMessage(); }
      catch { if (status) status.textContent = 'Não foi possível abrir as preferências. Tente novamente mais tarde.'; }
    });
  });
  async function start() {
    // Never contact advertising services from local development or previews.
    if (!['golguess.com.br', 'www.golguess.com.br'].includes(location.hostname)) return;
    try {
      const response = await fetch('/api/public_config', {cache:'no-store'});
      if (!response.ok) return;
      const config = await response.json();
      publish({config});
      if (!config.cmpEnabled || !config.cmpId) return;
      pause();
      window.googlefc = window.googlefc || {};
      window.googlefc.callbackQueue = window.googlefc.callbackQueue || [];
      window.googlefc.callbackQueue.push({CONSENT_API_READY: () => {
        if (typeof window.__tcfapi !== 'function') return;
        window.__tcfapi('addEventListener', 2, (tc, success) => {
          const valid = !!(success && tc?.cmpStatus === 'loaded' && String(tc.cmpId) === String(config.cmpId));
          regionalMessage = valid && tc.gdprApplies === true;
          // Conservative policy: unsupported regions and partial consent remain blocked.
          publish({allowed:!!(regionalMessage &&
            ['tcloaded','useractioncomplete'].includes(tc.eventStatus) && tc.tcString &&
            tc.vendor?.consents?.[755] && [1,3,4].every(id => tc.purpose?.consents?.[id]))});
        });
      }});
      const script = document.createElement('script');
      script.async = true;
      script.crossOrigin = 'anonymous';
      script.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6239237268971394';
      script.onload = () => publish({ready:true});
      script.onerror = () => publish({ready:false, allowed:false});
      document.head.append(script);
    } catch { publish({allowed:false}); }
  }
  start();
})();
