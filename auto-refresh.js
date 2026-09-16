(() => {
  const CHECK_EVERY_MS = 60_000;
  const BUILD_PATTERN = /Dashboard généré<br><b[^>]*>([^<]+)<\/b>/;
  const currentBuild = document.documentElement.innerHTML.match(BUILD_PATTERN)?.[1] || null;
  if (!currentBuild) return;

  let checking = false;
  async function checkForNewBuild() {
    if (checking || document.visibilityState !== 'visible') return;
    checking = true;
    try {
      const response = await fetch(`/?_version=${Date.now()}`, {
        cache: 'no-store',
        headers: { 'Cache-Control': 'no-cache' }
      });
      if (!response.ok) return;
      const html = await response.text();
      const remoteBuild = html.match(BUILD_PATTERN)?.[1] || null;
      if (remoteBuild && remoteBuild !== currentBuild) {
        window.location.reload();
      }
    } catch (_) {
      // A transient network error must never disturb the dashboard.
    } finally {
      checking = false;
    }
  }

  window.setInterval(checkForNewBuild, CHECK_EVERY_MS);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') checkForNewBuild();
  });
})();
