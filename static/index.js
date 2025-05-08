document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.welcome-effect').forEach(function(el) {
      el.innerHTML = el.textContent.split('').map(char =>
        char === ' ' ? '<span class="space">&nbsp;</span>' : `<span>${char}</span>`
      ).join('');
    });
  });
  