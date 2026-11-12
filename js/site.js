/* ============================================================
   Bloom & Budget — progressive enhancement
   Nav, share + copy link, blog search, TOC highlighting,
   newsletter signup. Everything works without JS except the
   search box, the copy button and the form feedback.
   ============================================================ */
(function () {
  "use strict";

  /* ---------------- mobile nav ---------------- */
  var toggle = document.querySelector(".nav-toggle");
  var navLinks = document.getElementById("navLinks");
  if (toggle && navLinks) {
    toggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });
  }

  /* ---------------- copy link ---------------- */
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.top = "-1000px";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        resolve();
      } catch (err) {
        reject(err);
      } finally {
        document.body.removeChild(ta);
      }
    });
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-copy-link]"),
    function (btn) {
      btn.addEventListener("click", function () {
        var bar = btn.closest(".share-bar");
        var url = bar ? bar.getAttribute("data-share-url") : window.location.href;
        var original = btn.textContent;
        copyText(url)
          .then(function () {
            btn.textContent = "Link copied";
            btn.classList.add("copied");
            window.setTimeout(function () {
              btn.textContent = original;
              btn.classList.remove("copied");
            }, 2400);
          })
          .catch(function () {
            window.prompt("Copy this link:", url);
          });
      });
    }
  );

  /* ---------------- blog search ---------------- */
  var search = document.querySelector("[data-post-search]");
  if (search) {
    var grid = document.querySelector("[data-post-grid]");
    var cards = grid
      ? Array.prototype.slice.call(grid.querySelectorAll(".post-card"))
      : [];
    var status = document.querySelector("[data-search-status]");
    var empty = document.querySelector("[data-no-results]");
    var haystack = cards.map(function (card) {
      return (card.textContent || "").toLowerCase().replace(/\s+/g, " ");
    });

    var runSearch = function () {
      var raw = search.value.trim();
      var q = raw.toLowerCase();
      var shown = 0;
      cards.forEach(function (card, i) {
        var hit = !q || haystack[i].indexOf(q) !== -1;
        card.hidden = !hit;
        if (hit) {
          shown += 1;
        }
      });
      if (status) {
        status.textContent = q
          ? shown +
            (shown === 1 ? " post matches \u201c" : " posts match \u201c") +
            raw +
            "\u201d"
          : "";
      }
      if (empty) {
        empty.hidden = shown !== 0;
      }
    };

    search.addEventListener("input", runSearch);
    search.addEventListener("search", runSearch);
    // Escape clears the box.
    search.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        search.value = "";
        runSearch();
      }
    });
  }

  /* ---------------- table of contents: active heading ---------------- */
  var tocLinks = Array.prototype.slice.call(
    document.querySelectorAll(".toc a[href^='#']")
  );
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (link) {
      var id = link.getAttribute("href").slice(1);
      var heading = document.getElementById(id);
      if (heading) {
        byId[id] = link;
      }
    });
    var visible = {};
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          visible[entry.target.id] = entry.isIntersecting;
        });
        var current = null;
        Object.keys(byId).forEach(function (id) {
          if (visible[id] && !current) {
            current = id;
          }
        });
        tocLinks.forEach(function (link) {
          link.classList.toggle(
            "active",
            current !== null && link.getAttribute("href") === "#" + current
          );
        });
      },
      { rootMargin: "-20% 0px -70% 0px", threshold: 0 }
    );
    Object.keys(byId).forEach(function (id) {
      observer.observe(document.getElementById(id));
    });
  }

  /* ---------------- newsletter ---------------- */
  function showMessage(box, kind, text) {
    var msg = box.querySelector("[data-form-msg]");
    if (!msg) {
      return;
    }
    msg.textContent = text;
    msg.classList.remove("is-success", "is-error");
    msg.classList.add(kind === "success" ? "is-success" : "is-error");
  }

  function subscribe(box, email) {
    var provider = (box.getAttribute("data-provider") || "").toLowerCase();
    var endpoint = (box.getAttribute("data-endpoint") || "").trim();

    if (!endpoint) {
      return Promise.reject(new Error("not-configured"));
    }

    if (provider === "formspree") {
      return fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json"
        },
        body: JSON.stringify({ email: email })
      }).then(function (res) {
        if (!res.ok) {
          throw new Error("request-failed");
        }
        return res.json().catch(function () {
          return {};
        });
      });
    }

    if (provider === "buttondown") {
      return fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "email=" + encodeURIComponent(email)
      }).then(function (res) {
        if (!res.ok && res.status !== 0) {
          throw new Error("request-failed");
        }
        return {};
      });
    }

    if (provider === "mailchimp") {
      return new Promise(function (resolve, reject) {
        var name = "mcCallback" + Math.floor(Math.random() * 1e6);
        var script = document.createElement("script");
        var timer = window.setTimeout(function () {
          cleanup();
          reject(new Error("request-failed"));
        }, 12000);
        function cleanup() {
          window.clearTimeout(timer);
          delete window[name];
          if (script.parentNode) {
            script.parentNode.removeChild(script);
          }
        }
        window[name] = function (data) {
          cleanup();
          if (data && data.result === "success") {
            resolve(data);
          } else {
            reject(new Error("request-failed"));
          }
        };
        script.src =
          endpoint +
          (endpoint.indexOf("?") === -1 ? "?" : "&") +
          "EMAIL=" +
          encodeURIComponent(email) +
          "&c=" +
          name;
        script.onerror = function () {
          cleanup();
          reject(new Error("request-failed"));
        };
        document.body.appendChild(script);
      });
    }

    return Promise.reject(new Error("unknown-provider"));
  }

  Array.prototype.forEach.call(
    document.querySelectorAll("[data-newsletter]"),
    function (box) {
      var form = box.querySelector(".newsletter-form");
      if (!form) {
        return;
      }
      var input = form.querySelector("input[type='email']");
      var button = form.querySelector("button");

      form.addEventListener("submit", function (event) {
        event.preventDefault();
        var email = (input && input.value || "").trim();

        if (!email || !input.checkValidity()) {
          showMessage(box, "error", "That email doesn't look right. Check it and try again.");
          if (input) {
            input.focus();
          }
          return;
        }

        var label = button ? button.textContent : "";
        if (button) {
          button.disabled = true;
          button.textContent = "Sending\u2026";
        }
        showMessage(box, "success", "");

        subscribe(box, email)
          .then(function () {
            showMessage(
              box,
              "success",
              "Almost there. Check your inbox and click the confirmation link to finish signing up."
            );
            form.reset();
          })
          .catch(function (err) {
            var text =
              err && err.message === "not-configured"
                ? "The signup box isn't connected yet. Please try again later."
                : "That didn't go through. Please try again in a moment.";
            showMessage(box, "error", text);
          })
          .then(function () {
            if (button) {
              button.disabled = false;
              button.textContent = label;
            }
          });
      });
    }
  );
})();
