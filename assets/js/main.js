/* COMandFIN site behaviour: navigation, LMS links, FAQ, enquiry form. */
(function () {
  "use strict";
  var cfg = window.SITE_CONFIG || {};
  var lms = cfg.lms || {};
  var contact = cfg.contact || {};

  /* Path prefix so links work from /courses/*.html and from the root */
  var root = document.documentElement.getAttribute("data-root") || "";

  function enquiryUrl(course) {
    return root + "index.html" + (course ? "?course=" + encodeURIComponent(course) : "") + "#contact";
  }

  function setLink(el, url) {
    el.setAttribute("href", url);
    if (/^https?:/i.test(url) && lms.openInNewTab) {
      el.setAttribute("target", "_blank");
      el.setAttribute("rel", "noopener");
    }
  }

  /* ---------- LMS buttons ----------
     data-lms="login"                  -> lms.loginUrl
     data-lms="signup"                 -> lms.signupUrl
     data-lms="course" data-course=ID  -> lms.courseUrls[ID]
     Empty URLs fall back to the enquiry form, so no button is ever dead. */
  document.querySelectorAll("[data-lms]").forEach(function (el) {
    var type = el.getAttribute("data-lms");
    var course = el.getAttribute("data-course");
    var url = "";
    if (type === "login") url = lms.loginUrl;
    else if (type === "signup") url = lms.signupUrl;
    else if (type === "course") url = (lms.courseUrls || {})[course];
    setLink(el, url || enquiryUrl(course));
  });

  document.querySelectorAll("[data-lms-name]").forEach(function (el) {
    if (lms.name) el.textContent = lms.name;
  });

  /* ---------- Contact details ---------- */
  document.querySelectorAll("[data-contact]").forEach(function (el) {
    var key = el.getAttribute("data-contact");
    var val = contact[key];
    if (!val) { el.closest("[data-contact-wrap]") && (el.closest("[data-contact-wrap]").hidden = true); return; }
    el.textContent = val;
    if (el.tagName === "A") {
      if (key === "email") el.href = "mailto:" + val;
      if (key === "phone") el.href = "tel:" + val.replace(/\s+/g, "");
    }
  });

  var wa = document.querySelector("[data-whatsapp]");
  if (wa) {
    if (contact.whatsapp) {
      wa.href = "https://wa.me/" + contact.whatsapp + "?text=" + encodeURIComponent("Hi COMandFIN, I would like to know more about your courses.");
      wa.hidden = false;
    } else wa.hidden = true;
  }

  document.querySelectorAll("[data-social]").forEach(function (el) {
    var url = (cfg.social || {})[el.getAttribute("data-social")];
    if (url) el.href = url; else el.hidden = true;
  });

  /* ---------- Mobile navigation ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---------- Header shadow on scroll ---------- */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("scrolled", window.scrollY > 8); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll(".faq-q").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var item = btn.parentElement;
      var open = item.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });

  /* ---------- Course filter tabs (home page) ---------- */
  var tabs = document.querySelectorAll(".filter-tab");
  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      var f = tab.getAttribute("data-filter");
      tabs.forEach(function (t) { t.classList.toggle("active", t === tab); t.setAttribute("aria-selected", t === tab ? "true" : "false"); });
      document.querySelectorAll(".course-card").forEach(function (card) {
        card.hidden = !(f === "all" || card.getAttribute("data-category") === f);
      });
    });
  });

  /* ---------- Enquiry form ---------- */
  var form = document.getElementById("enquiry-form");
  if (form) {
    var params = new URLSearchParams(window.location.search);
    var pre = params.get("course");
    var sel = form.querySelector("select[name=course]");
    if (pre && sel) {
      Array.prototype.forEach.call(sel.options, function (o) { if (o.value === pre) sel.value = pre; });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var status = form.querySelector(".form-status");
      var data = new FormData(form);
      if (data.get("company")) return; // honeypot

      if (cfg.formEndpoint) {
        status.textContent = "Sending…";
        fetch(cfg.formEndpoint, { method: "POST", body: data, headers: { Accept: "application/json" } })
          .then(function (r) {
            if (!r.ok) throw new Error();
            form.reset();
            status.textContent = "Thank you. Our academic counsellor will contact you shortly.";
          })
          .catch(function () {
            status.textContent = "Something went wrong. Please email us at " + (contact.email || "") + ".";
          });
      } else {
        var body = "Name: " + data.get("name") + "\nEmail: " + data.get("email") + "\nPhone: " + data.get("phone") +
          "\nCourse: " + data.get("course") + "\n\n" + (data.get("message") || "");
        window.location.href = "mailto:" + (contact.email || "") + "?subject=" +
          encodeURIComponent("Course enquiry: " + data.get("course")) + "&body=" + encodeURIComponent(body);
        status.textContent = "Opening your email app…";
      }
    });
  }

  /* ---------- Footer year ---------- */
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
