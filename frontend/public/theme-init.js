;(function () {
  try {
    var stored = localStorage.getItem('timegrip-theme')
    var isDark =
      stored === 'dark' ||
      (stored !== 'light' &&
        window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', isDark)
  } catch (e) {}

  try {
    var media = window.matchMedia('(prefers-color-scheme: dark)')
    var favicon = document.getElementById('favicon')
    function applyFavicon() {
      favicon.href = media.matches ? '/favicon-dark.ico' : '/favicon-light.ico'
    }
    applyFavicon()
    media.addEventListener('change', applyFavicon)
  } catch (e) {}
})()
