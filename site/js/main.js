(function () {
  var desktopMQ = window.matchMedia('(min-width: 901px)');

  // Escala a réplica desktop (1440px) para a largura da janela, como o Canva faz.
  var desk = document.querySelector('.desk');
  function fit() {
    if (!desk) return;
    desk.style.setProperty('--z', (document.documentElement.clientWidth / 1440).toFixed(5));
  }

  // As mídias do desktop vêm com data-src; só carregam quando o layout desktop está ativo,
  // assim o celular não baixa as imagens que não vai mostrar.
  var deskLoaded = false;
  function loadDesk() {
    if (deskLoaded || !desk || !desktopMQ.matches) return;
    deskLoaded = true;
    desk.querySelectorAll('[data-src]').forEach(function (el) {
      el.src = el.getAttribute('data-src');
      el.removeAttribute('data-src');
    });
    watchVideos(desk.querySelectorAll('video'));
  }

  // Vídeos só tocam quando visíveis.
  var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { var p = en.target.play(); if (p && p.catch) p.catch(function () {}); }
      else en.target.pause();
    });
  }, { threshold: 0.15 }) : null;
  function watchVideos(list) {
    list.forEach(function (v) {
      v.muted = true;
      if (io) io.observe(v); else v.play();
    });
  }

  fit();
  loadDesk();
  watchVideos(document.querySelectorAll('.mob video'));
  window.addEventListener('resize', function () { fit(); loadDesk(); });

  // Menu do mobile
  var btn = document.querySelector('.m-menu-btn');
  function setMenu(open) {
    document.body.classList.toggle('menu-open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (btn) {
    btn.addEventListener('click', function () { setMenu(!document.body.classList.contains('menu-open')); });
    document.querySelectorAll('.m-menu a').forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && document.body.classList.contains('menu-open')) { setMenu(false); btn.focus(); }
    });
  }
})();
