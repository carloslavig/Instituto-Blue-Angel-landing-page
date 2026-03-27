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
    '.gallery-item, .donation-option, .pillar'
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

  /* ── 5. Seleção de valores de doação ───────────────────── */
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

  /* ── 6. Formulário de contato ──────────────────────────── */
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

  /* ── 7. Máscara de telefone ─────────────────────────────── */
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

  /* ── 8. Destaque do link ativo na navegação ─────────────── */
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

});
