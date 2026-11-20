/* Orbit v7 offline shell — MathJax is bundled locally for offline TeX rendering. */
'use strict';
const CACHE_NAME = 'orbit-shell-v5-offline-math';
const APP_SHELL = ["./","./index.html","./manifest.webmanifest","./icon.svg","./icon-192.png","./icon-512.png","./vendor/mathjax/es5/a11y/assistive-mml.js","./vendor/mathjax/es5/a11y/complexity.js","./vendor/mathjax/es5/a11y/explorer.js","./vendor/mathjax/es5/a11y/semantic-enrich.js","./vendor/mathjax/es5/a11y/sre.js","./vendor/mathjax/es5/adaptors/liteDOM.js","./vendor/mathjax/es5/core.js","./vendor/mathjax/es5/input/asciimath.js","./vendor/mathjax/es5/input/mml/entities.js","./vendor/mathjax/es5/input/mml/extensions/mml3.js","./vendor/mathjax/es5/input/mml/extensions/mml3.sef.json","./vendor/mathjax/es5/input/mml.js","./vendor/mathjax/es5/input/tex/extensions/action.js","./vendor/mathjax/es5/input/tex/extensions/all-packages.js","./vendor/mathjax/es5/input/tex/extensions/ams.js","./vendor/mathjax/es5/input/tex/extensions/amscd.js","./vendor/mathjax/es5/input/tex/extensions/autoload.js","./vendor/mathjax/es5/input/tex/extensions/bbox.js","./vendor/mathjax/es5/input/tex/extensions/boldsymbol.js","./vendor/mathjax/es5/input/tex/extensions/braket.js","./vendor/mathjax/es5/input/tex/extensions/bussproofs.js","./vendor/mathjax/es5/input/tex/extensions/cancel.js","./vendor/mathjax/es5/input/tex/extensions/cases.js","./vendor/mathjax/es5/input/tex/extensions/centernot.js","./vendor/mathjax/es5/input/tex/extensions/color.js","./vendor/mathjax/es5/input/tex/extensions/colortbl.js","./vendor/mathjax/es5/input/tex/extensions/colorv2.js","./vendor/mathjax/es5/input/tex/extensions/configmacros.js","./vendor/mathjax/es5/input/tex/extensions/empheq.js","./vendor/mathjax/es5/input/tex/extensions/enclose.js","./vendor/mathjax/es5/input/tex/extensions/extpfeil.js","./vendor/mathjax/es5/input/tex/extensions/gensymb.js","./vendor/mathjax/es5/input/tex/extensions/html.js","./vendor/mathjax/es5/input/tex/extensions/mathtools.js","./vendor/mathjax/es5/input/tex/extensions/mhchem.js","./vendor/mathjax/es5/input/tex/extensions/newcommand.js","./vendor/mathjax/es5/input/tex/extensions/noerrors.js","./vendor/mathjax/es5/input/tex/extensions/noundefined.js","./vendor/mathjax/es5/input/tex/extensions/physics.js","./vendor/mathjax/es5/input/tex/extensions/require.js","./vendor/mathjax/es5/input/tex/extensions/setoptions.js","./vendor/mathjax/es5/input/tex/extensions/tagformat.js","./vendor/mathjax/es5/input/tex/extensions/textcomp.js","./vendor/mathjax/es5/input/tex/extensions/textmacros.js","./vendor/mathjax/es5/input/tex/extensions/unicode.js","./vendor/mathjax/es5/input/tex/extensions/upgreek.js","./vendor/mathjax/es5/input/tex/extensions/verb.js","./vendor/mathjax/es5/input/tex-base.js","./vendor/mathjax/es5/input/tex-full.js","./vendor/mathjax/es5/input/tex.js","./vendor/mathjax/es5/latest.js","./vendor/mathjax/es5/loader.js","./vendor/mathjax/es5/mml-chtml.js","./vendor/mathjax/es5/mml-svg.js","./vendor/mathjax/es5/node-main.js","./vendor/mathjax/es5/output/chtml/fonts/tex.js","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_AMS-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Calligraphic-Bold.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Calligraphic-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Fraktur-Bold.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Fraktur-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Main-Bold.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Main-Italic.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Main-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Math-BoldItalic.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Math-Italic.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Math-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_SansSerif-Bold.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_SansSerif-Italic.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_SansSerif-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Script-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Size1-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Size2-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Size3-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Size4-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Typewriter-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Vector-Bold.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Vector-Regular.woff","./vendor/mathjax/es5/output/chtml/fonts/woff-v2/MathJax_Zero.woff","./vendor/mathjax/es5/output/chtml.js","./vendor/mathjax/es5/output/svg/fonts/tex.js","./vendor/mathjax/es5/output/svg.js","./vendor/mathjax/es5/sre/mathmaps/base.json","./vendor/mathjax/es5/sre/mathmaps/ca.json","./vendor/mathjax/es5/sre/mathmaps/da.json","./vendor/mathjax/es5/sre/mathmaps/de.json","./vendor/mathjax/es5/sre/mathmaps/en.json","./vendor/mathjax/es5/sre/mathmaps/es.json","./vendor/mathjax/es5/sre/mathmaps/fr.json","./vendor/mathjax/es5/sre/mathmaps/hi.json","./vendor/mathjax/es5/sre/mathmaps/it.json","./vendor/mathjax/es5/sre/mathmaps/nb.json","./vendor/mathjax/es5/sre/mathmaps/nemeth.json","./vendor/mathjax/es5/sre/mathmaps/nn.json","./vendor/mathjax/es5/sre/mathmaps/sv.json","./vendor/mathjax/es5/startup.js","./vendor/mathjax/es5/tex-chtml-full-speech.js","./vendor/mathjax/es5/tex-chtml-full.js","./vendor/mathjax/es5/tex-chtml.js","./vendor/mathjax/es5/tex-mml-chtml.js","./vendor/mathjax/es5/tex-mml-svg.js","./vendor/mathjax/es5/tex-svg-full.js","./vendor/mathjax/es5/tex-svg.js","./vendor/mathjax/es5/ui/lazy.js","./vendor/mathjax/es5/ui/menu.js","./vendor/mathjax/es5/ui/safe.js"];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    // Cache app shell and all MathJax JS, extensions, accessibility resources and local fonts.
    // A complete successful install is required; no half-installed offline math runtime.
    await cache.addAll(APP_SHELL);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key.startsWith('orbit-shell-') && key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  // Keep existing on-demand caching for other optional tools (for example Anki APKG import).
  if (url.origin !== self.location.origin) {
    if (!/^https?:$/.test(url.protocol) || !/cdn\.jsdelivr\.net$/.test(url.hostname)) return;
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      if (cached) return cached;
      try {
        const response = await fetch(request);
        if (response && (response.ok || response.type === 'opaque')) await cache.put(request, response.clone());
        return response;
      } catch (error) {
        const fallback = await cache.match(request);
        if (fallback) return fallback;
        throw error;
      }
    })());
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response && response.ok) caches.open(CACHE_NAME).then(cache => cache.put('./index.html', response.clone()));
          return response;
        })
        .catch(() => caches.match('./index.html').then(response => response || caches.match('./')))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        if (response && response.ok && response.type === 'basic') {
          caches.open(CACHE_NAME).then(cache => cache.put(request, response.clone()));
        }
        return response;
      });
    })
  );
});
