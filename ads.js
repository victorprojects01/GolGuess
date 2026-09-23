// Ad requests require eligible content and verified consent; CMP bootstrap stays paused.
(() => {
  const slot = document.querySelector('.ad-slot, .ranking-ad');
  if (!slot) return;
  let eligible = false, consent = false, requested = false, config;
  let ready = false;
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
  function update() {
    if (!eligible || !consent || !ready || !config?.adsEnabled || document.querySelector('dialog[open]')) {
      window.golguessConsent?.pause(); suppress(); return;
    }
    if (slot.dataset.unfilled !== undefined) return;
    slot.hidden = false;
    delete slot.dataset.suppressed;
    const ads = window.adsbygoogle = window.adsbygoogle || [];
    ads.pauseAdRequests = 0;
    if (requested) return;
    requested = true; // Never refresh on guesses, mode changes or timers.
    reserveGame();
    try { ads.push({}); }
    catch { window.golguessConsent?.pause(); suppress(); }
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
  window.golguessConsent?.subscribe(state => {
    consent = state.allowed; ready = state.ready; config = state.config;
    update();
  });
})();
