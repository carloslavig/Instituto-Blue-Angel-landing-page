/* ============================================================
   Instituto Blue Angel's — Script Principal
   Arquivo: js/main.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {

  /* ── 1. Navbar: sombra ao rolar ────────────────────────── */
  const navbar = document.getElementById('navbar');

  window.addEventListener('scroll', function () {
    if (window.scrollY > 10) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  /* ── 2. Menu mobile (hambúrguer) ───────────────────────── */
  const hamburger = document.getElementById('hamburger');
  const navLinks  = document.getElementById('navLinks');

  hamburger.addEventListener('click', function () {
    hamburger.classList.toggle('open');
    navLinks.classList.toggle('open');
  });

  // Fecha o menu ao clicar em um link
  navLinks.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      hamburger.classList.remove('open');
      navLinks.classList.remove('open');
    });
  });

  // Fecha o menu ao clicar fora
  document.addEventListener('click', function (e) {
    if (!navbar.contains(e.target)) {
      hamburger.classList.remove('open');
      navLinks.classList.remove('open');
    }
  });

  /* ── 3. Scroll suave para âncoras ──────────────────────── */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (!target) return;

      e.preventDefault();
      const navHeight = navbar.offsetHeight;
      const targetPos = target.getBoundingClientRect().top + window.scrollY - navHeight - 12;

      window.scrollTo({ top: targetPos, behavior: 'smooth' });
    });
  });

  /* ── 4. Animação de entrada (fade-in ao rolar) ─────────── */
  const fadeEls = document.querySelectorAll(
    '.service-card, .team-card, .about-grid, .contact-item, ' +
    '.gallery-item, .donation-option, .pillar, .partner-card'
  );

  // Adiciona a classe base a todos os elementos animáveis
  fadeEls.forEach(function (el) {
    el.classList.add('fade-in');
  });

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target); // anima só uma vez
      }
    });
  }, { threshold: 0.12 });

  fadeEls.forEach(function (el) {
    observer.observe(el);
  });

/* ── 5. Carrossel da Equipe ─────────────────────────────── */
(function () {
  var track    = document.getElementById('teamTrack');
  var viewport = document.getElementById('teamViewport');
  var dotsEl   = document.getElementById('teamDots');
  var btnPrev  = document.getElementById('teamPrev');
  var btnNext  = document.getElementById('teamNext');

  if (!track) return;

  var cards        = Array.from(track.children);
  var current      = 0;
  var autoplayTimer;
  var AUTOPLAY_MS  = 4000;

  /* Quantos cards cabem visíveis por vez */
  function perView() {
    var w = viewport.offsetWidth;
    if (w <= 520) return 1;
    if (w <= 860) return 2;
    return 3;
  }

  /* Total de "páginas" (posições de parada) */
  function maxIndex() {
    return Math.max(0, cards.length - perView());
  }

  /* Largura de um card + gap em px */
  function stepPx() {
    var card = cards[0];
    var gap  = parseFloat(getComputedStyle(track).gap) || 24;
    return card.offsetWidth + gap;
  }

  /* Move o track */
  function goTo(index) {
    current = Math.max(0, Math.min(index, maxIndex()));
    track.style.transform = 'translateX(-' + (current * stepPx()) + 'px)';
    updateUI();
  }

  /* Atualiza botões e dots */
  function updateUI() {
    btnPrev.disabled = current === 0;
    btnNext.disabled = current >= maxIndex();

    var dots = dotsEl.querySelectorAll('.team-dot');
    dots.forEach(function (d, i) { d.classList.toggle('active', i === current); });
  }

  /* Gera dots */
  function buildDots() {
    dotsEl.innerHTML = '';
    var total = maxIndex() + 1;
    for (var i = 0; i < total; i++) {
      var btn = document.createElement('button');
      btn.className   = 'team-dot';
      btn.setAttribute('aria-label', 'Ir para slide ' + (i + 1));
      btn.dataset.idx = i;
      btn.addEventListener('click', function () {
        goTo(parseInt(this.dataset.idx));
        resetAutoplay();
      });
      dotsEl.appendChild(btn);
    }
    updateUI();
  }

  /* Autoplay */
  function startAutoplay() {
    autoplayTimer = setInterval(function () {
      goTo(current >= maxIndex() ? 0 : current + 1);
    }, AUTOPLAY_MS);
  }

  function resetAutoplay() {
    clearInterval(autoplayTimer);
    startAutoplay();
  }

  /* Botões */
  btnPrev.addEventListener('click', function () { goTo(current - 1); resetAutoplay(); });
  btnNext.addEventListener('click', function () { goTo(current + 1); resetAutoplay(); });

  /* Teclado (quando o carrossel está em foco) */
  viewport.setAttribute('tabindex', '0');
  viewport.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft')  { goTo(current - 1); resetAutoplay(); }
    if (e.key === 'ArrowRight') { goTo(current + 1); resetAutoplay(); }
  });

  /* Swipe mobile */
  var touchStartX = 0;
  track.addEventListener('touchstart', function (e) {
    touchStartX = e.touches[0].clientX;
  }, { passive: true });

  track.addEventListener('touchend', function (e) {
    var delta = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(delta) > 40) {
      goTo(delta > 0 ? current + 1 : current - 1);
      resetAutoplay();
    }
  }, { passive: true });

  /* Pausa ao passar o mouse */
  viewport.addEventListener('mouseenter', function () { clearInterval(autoplayTimer); });
  viewport.addEventListener('mouseleave', startAutoplay);

  /* Reconstrói dots ao redimensionar */
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      goTo(Math.min(current, maxIndex()));
      buildDots();
    }, 150);
  });

  /* Init */
  buildDots();
  startAutoplay();
}());
/* ── fim carrossel equipe ─────────────────────────────────── */


  /* ── 6. Seleção de valores de doação ───────────────────── */
  const donationOptions = document.querySelectorAll('.donation-option');

  donationOptions.forEach(function (option) {
    option.addEventListener('click', function () {
      // Remove seleção de todos
      donationOptions.forEach(function (o) {
        o.classList.remove('selected');
        o.querySelector('.donation-check').textContent = '';
      });

      // Aplica seleção ao clicado
      this.classList.add('selected');
      this.querySelector('.donation-check').textContent = '✓';
    });
  });

  /* ── 7. Formulário de contato ──────────────────────────── */
  const contactForm    = document.getElementById('contactForm');
  const formFeedback   = document.getElementById('formFeedback');

  if (contactForm) {
    contactForm.addEventListener('submit', function (e) {
      e.preventDefault();

      // Validação básica
      const nome     = document.getElementById('nome').value.trim();
      const email    = document.getElementById('email').value.trim();
      const mensagem = document.getElementById('mensagem').value.trim();

      if (!nome || !email || !mensagem) {
        showFeedback('Por favor, preencha todos os campos obrigatórios.', 'error');
        return;
      }

      if (!isValidEmail(email)) {
        showFeedback('Por favor, insira um e-mail válido.', 'error');
        return;
      }

      /*
       * ── INTEGRAÇÃO DE ENVIO ──────────────────────────────
       * Opções para enviar o formulário:
       *
       * OPÇÃO A — Formspree (gratuito, sem back-end):
       *   1. Crie uma conta em https://formspree.io
       *   2. Obtenha seu endpoint (ex: https://formspree.io/f/xyzabcde)
       *   3. Substitua a URL abaixo e descomente o bloco.
       *
       * OPÇÃO B — EmailJS (gratuito até 200 emails/mês):
       *   1. Crie uma conta em https://www.emailjs.com
       *   2. Configure o serviço e template
       *   3. Use a SDK deles para enviar.
       *
       * OPÇÃO C — WhatsApp direto (mais simples):
       *   Descomente o bloco de WhatsApp abaixo.
       * ───────────────────────────────────────────────────── */

      // --- OPÇÃO A: Formspree (descomente e ajuste a URL) ---
      /*
      const formData = new FormData(contactForm);
      fetch('https://formspree.io/f/SEU_ID_AQUI', {
        method: 'POST',
        body: formData,
        headers: { 'Accept': 'application/json' }
      })
      .then(function (res) {
        if (res.ok) {
          showFeedback('✅ Mensagem enviada! Entraremos em contato em breve.', 'success');
          contactForm.reset();
        } else {
          showFeedback('Erro ao enviar. Tente novamente ou entre em contato pelo WhatsApp.', 'error');
        }
      })
      .catch(function () {
        showFeedback('Erro de conexão. Verifique sua internet e tente novamente.', 'error');
      });
      return;
      */

      // --- OPÇÃO C: Redireciona para WhatsApp (ativo por padrão) ---
      var assunto  = document.getElementById('assunto').value;
      var telefone = document.getElementById('telefone').value.trim();
      var texto    = encodeURIComponent(
        '🕊️ *Contato pelo site — Instituto Blue Angel\'s*\n\n' +
        '*Nome:* ' + nome + '\n' +
        '*E-mail:* ' + email + '\n' +
        (telefone ? '*Telefone:* ' + telefone + '\n' : '') +
        '*Assunto:* ' + assunto + '\n\n' +
        '*Mensagem:*\n' + mensagem
      );

      // ⚠️ Substitua pelo número real com DDI (55 = Brasil)
      var whatsappNum = '5521999999999';
      window.open('https://wa.me/' + whatsappNum + '?text=' + texto, '_blank');

      showFeedback('✅ Você será redirecionado ao WhatsApp para enviar sua mensagem.', 'success');
      contactForm.reset();
    });
  }

  function showFeedback(msg, type) {
    formFeedback.textContent = msg;
    formFeedback.className   = 'form-feedback ' + type;
    setTimeout(function () {
      formFeedback.textContent = '';
      formFeedback.className   = 'form-feedback';
    }, 6000);
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  /* ── 8. Máscara de telefone ─────────────────────────────── */
  var telefoneInput = document.getElementById('telefone');
  if (telefoneInput) {
    telefoneInput.addEventListener('input', function () {
      var v = this.value.replace(/\D/g, '').substring(0, 11);
      if (v.length <= 10) {
        v = v.replace(/^(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
      } else {
        v = v.replace(/^(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
      }
      this.value = v;
    });
  }

  /* ── 9. Destaque do link ativo na navegação ─────────────── */
  var sections = document.querySelectorAll('section[id], div[id]');
  var navItems = document.querySelectorAll('.nav-links a[href^="#"]');

  window.addEventListener('scroll', function () {
    var scrollPos = window.scrollY + navbar.offsetHeight + 40;

    sections.forEach(function (section) {
      if (
        section.offsetTop <= scrollPos &&
        section.offsetTop + section.offsetHeight > scrollPos
      ) {
        navItems.forEach(function (link) {
          link.style.color = '';
        });
        var activeLink = document.querySelector('.nav-links a[href="#' + section.id + '"]');
        if (activeLink && !activeLink.classList.contains('nav-cta')) {
          activeLink.style.color = 'var(--accent)';
        }
      }
    });
  });

  /* ── 10. Efeito Typewriter no Hero ─────────────────────── */
  const typewriter = document.getElementById('typewriter');
  if (typewriter) {
    const words = ["transformar vidas", "acolher famílias", "mudar futuros", "incluir com amor"];
    let wordIdx = 0;
    let charIdx = 0;
    let isDeleting = false;

    function type() {
      const currentWord = words[wordIdx];
      if (isDeleting) {
        typewriter.textContent = currentWord.substring(0, charIdx - 1);
        charIdx--;
      } else {
        typewriter.textContent = currentWord.substring(0, charIdx + 1);
        charIdx++;
      }

      let typeSpeed = isDeleting ? 50 : 100;
      if (!isDeleting && charIdx === currentWord.length) {
        isDeleting = true;
        typeSpeed = 2000; // Pausa no final da palavra
      } else if (isDeleting && charIdx === 0) {
        isDeleting = false;
        wordIdx = (wordIdx + 1) % words.length;
        typeSpeed = 500;
      }
      setTimeout(type, typeSpeed);
    }
    type();
  }

  /* ── 11. Contador de Estatísticas ──────────────────────── */
  const statsSection = document.querySelector('.hero-stats');
  const stats = document.querySelectorAll('.stat-num');
  let started = false;

  const startCount = () => {
    stats.forEach(stat => {
      const target = parseInt(stat.dataset.target);
      const prefix = stat.dataset.prefix || '';
      const suffix = stat.dataset.suffix || '';
      let count = 0;
      const increment = target / 50;
      const timer = setInterval(() => {
        count += increment;
        if (count >= target) {
          stat.textContent = prefix + target + suffix;
          clearInterval(timer);
        } else {
          stat.textContent = prefix + Math.floor(count) + suffix;
        }
      }, 30);
    });
  };

  const statsObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !started) {
      startCount();
      started = true;
    }
  }, { threshold: 0.5 });
  if (statsSection) statsObserver.observe(statsSection);

});

/* ── 12. Função de Copiar (Global) ──────────────────────── */
function copyToClipboard(elementId, btn) {
  const text = document.getElementById(elementId).innerText;
  navigator.clipboard.writeText(text).then(() => {
    const originalText = btn.innerText;
    btn.innerText = 'Copiado!';
    btn.style.background = '#1a7a3c';
    btn.style.color = '#fff';
    setTimeout(() => {
      btn.innerText = originalText;
      btn.style.background = '';
      btn.style.color = '';
    }, 2000);
  });
}
