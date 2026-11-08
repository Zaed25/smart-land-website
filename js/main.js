// Smart Land - small scripts shared by all pages (no libraries)
document.addEventListener("DOMContentLoaded", () => {
  // 1. mobile menu
  const toggle = document.querySelector(".nav__toggle");
  const links = document.querySelector(".nav__links");
  if (toggle && links) {
    toggle.addEventListener("click", () => {
      const open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open);
    });
  }

  // 2. header shadow + "back to top" button after scrolling
  const header = document.querySelector(".site-header");
  const toTop = document.querySelector(".to-top");
  const onScroll = () => {
    header.classList.toggle("scrolled", window.scrollY > 10);
    if (toTop) toTop.classList.toggle("show", window.scrollY > 600);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  // 3. show sections when they enter the screen
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("visible");
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.15 });
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

  // 4. counters in the statistics bar (count up once)
  // (skipped when the visitor asked the system for reduced motion: the final numbers are already in the HTML)
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const counters = reduced ? [] : document.querySelectorAll("[data-count]");
  const countIO = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      const el = e.target;
      const end = Number(el.dataset.count);
      const plus = el.dataset.plus || "";
      const start = performance.now();
      const step = (now) => {
        const p = Math.min((now - start) / 1400, 1);
        el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3))) + plus;
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
      countIO.unobserve(el);
    });
  }, { threshold: 0.6 });
  counters.forEach((c) => countIO.observe(c));

  // 5. modals (project details and videos)
  const openModal = (modal) => {
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    modal.querySelector(".modal__close").focus();
  };
  const closeModal = (modal) => {
    modal.classList.remove("open");
    document.body.style.overflow = "";
    modal.querySelectorAll("video").forEach((v) => v.pause());
  };
  document.querySelectorAll(".modal").forEach((m) => {
    m.addEventListener("click", (e) => { if (e.target === m || e.target.closest(".modal__close")) closeModal(m); });
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") document.querySelectorAll(".modal.open").forEach(closeModal);
  });

  // video buttons: <button data-video="intro"> opens #video-modal with that file
  const vModal = document.getElementById("video-modal");
  document.querySelectorAll("[data-video]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const v = vModal.querySelector("video");
      const name = btn.dataset.video;
      v.poster = `assets/video/${name}-poster.webp`;
      v.querySelector("source").src = `assets/video/${name}.mp4`;
      v.querySelector("track").src = `assets/video/${name}.vtt`;
      v.load();
      openModal(vModal);
      v.play().catch(() => {});
    });
  });

  // project cards: fill #project-modal from the card content
  // (only on projects.html, where the cards carry data-cat and a <template> with the long text)
  const pModal = document.getElementById("project-modal");
  if (pModal) {
    document.querySelectorAll(".project[data-cat]").forEach((card) => {
      const show = () => {
        const media = card.querySelector("picture, .art").cloneNode(true);
        pModal.querySelector(".modal__media").replaceChildren(media);
        pModal.querySelector("h3").textContent = card.querySelector("h3").textContent;
        pModal.querySelector(".modal__desc").innerHTML = card.querySelector("template").innerHTML;
        openModal(pModal);
      };
      card.addEventListener("click", show);
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); show(); }
      });
    });
  }

  // 6. project filter
  document.querySelectorAll(".filters button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filters button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const f = btn.dataset.filter;
      document.querySelectorAll(".project[data-cat]").forEach((p) => {
        p.classList.toggle("hide", f !== "all" && !p.dataset.cat.split(" ").includes(f));
      });
    });
  });

  // 7. contact form: check the fields in the browser (static site, nothing is sent to a server)
  const form = document.querySelector(".form");
  if (form) {
    const rules = {
      name: (v) => v.trim().length >= 3 || "اكتب اسمك (3 أحرف على الأقل)",
      email: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) || "البريد الإلكتروني غير صحيح",
      topic: (v) => v !== "" || "اختر موضوع الرسالة",
      message: (v) => v.trim().length >= 15 || "الرسالة قصيرة جداً (15 حرفاً على الأقل)",
    };
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      let ok = true;
      Object.entries(rules).forEach(([name, test]) => {
        const field = form.elements[name];
        const res = test(field.value);
        const err = form.querySelector(`#${name}-error`);
        field.classList.toggle("invalid", res !== true);
        err.textContent = res === true ? "" : res;
        if (res !== true) ok = false;
      });
      if (ok) {
        form.reset();
        document.querySelector(".form-success").classList.add("show");
      }
    });
  }

  // 8. year in the footer
  document.querySelectorAll(".year").forEach((y) => (y.textContent = new Date().getFullYear()));
});
