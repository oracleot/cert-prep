function initTimers() {
  document.querySelectorAll('[data-timer-minutes]').forEach((box) => {
    const minutes = Number(box.getAttribute('data-timer-minutes') || '0');
    const display = box.querySelector('[data-timer-display]');
    const start = box.querySelector('[data-timer-start]');
    const reset = box.querySelector('[data-timer-reset]');
    let remaining = minutes * 60;
    let timerId = null;

    function render() {
      const mins = Math.floor(remaining / 60).toString().padStart(2, '0');
      const secs = (remaining % 60).toString().padStart(2, '0');
      display.textContent = `${mins}:${secs}`;
    }

    function stop() {
      if (timerId) clearInterval(timerId);
      timerId = null;
    }

    start.addEventListener('click', () => {
      if (timerId) return;
      timerId = setInterval(() => {
        remaining -= 1;
        render();
        if (remaining <= 0) {
          stop();
          box.classList.add('done');
          display.textContent = 'Time!';
        }
      }, 1000);
    });

    reset.addEventListener('click', () => {
      stop();
      box.classList.remove('done');
      remaining = minutes * 60;
      render();
    });

    render();
  });
}

initTimers();
