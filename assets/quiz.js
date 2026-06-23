/**
 * Quiz interaction — legacy choose() plus enhanced walkthrough reveal.
 * Walkthrough mode (data-walkthrough="true"): rationale, explanation, and
 * knowledge-gap asides are hidden until the user selects an answer, then
 * revealed inline so the stem and all options remain visible.
 *
 * DOMContentLoaded initialisation (walkthrough mode):
 *   - infers the correct answer label from the button with data-correct
 *     by reading its leading A)/B)/C)/D) prefix, falling back to DOM order
 *   - assigns data-answer="A|B|C|D" to all .choice buttons when missing
 *   - attaches click listeners that call choose(button, answerLabel)
 *   - skips buttons that already carry an inline onclick to avoid double-fire
 */
function choose(button, expected, answerLabel) {
  const quiz = button.closest('[data-quiz]');
  const feedback = quiz.querySelector('[data-feedback]');
  const selected = button.dataset.answer;
  const correct = selected === expected;

  quiz.querySelectorAll('button.choice').forEach((choice) => {
    choice.disabled = true;
  });

  feedback.textContent = correct
    ? 'Correct. Keep the keyword-to-service link.'
    : `Not yet. Best answer: ${expected}.`;
  feedback.className = `feedback ${correct ? 'ok' : 'bad'}`;

  if (quiz.dataset.walkthrough !== 'true') return;

  // Reveal rationale, explanation, and knowledge-gap asides in walkthrough mode
  quiz.querySelectorAll('aside[data-rationale-for], aside.explanation, aside.knowledge-gap').forEach((aside) => {
    aside.hidden = false;
    aside.classList.add('revealed');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  // ── 1. Hide walkthrough asides on load ─────────────────────────────────
  const asideSelector =
    'section[data-quiz][data-walkthrough="true"] aside[data-rationale-for], ' +
    'section[data-quiz][data-walkthrough="true"] aside.explanation, ' +
    'section[data-quiz][data-walkthrough="true"] aside.knowledge-gap';
  document.querySelectorAll(asideSelector).forEach((aside) => {
    aside.hidden = true;
  });

  // ── 2. Wire walkthrough section buttons ────────────────────────────────
  document.querySelectorAll('section[data-quiz][data-walkthrough="true"]').forEach((section) => {
    const buttons = Array.from(section.querySelectorAll('button.choice'));
    if (buttons.length === 0) return;

    // Find the correct answer label from the button with data-correct
    const correctBtn = buttons.find((b) => b.hasAttribute('data-correct'));
    let correctLabel = null;

    if (correctBtn) {
      // Prefer leading A)/B)/C)/D) prefix; fall back to positional index
      const match = correctBtn.textContent.trim().match(/^([A-D])\)/);
      if (match) {
        correctLabel = match[1];
      } else {
        const idx = buttons.indexOf(correctBtn);
        correctLabel = String.fromCharCode(65 + idx); // A, B, C, D
      }
    }

    buttons.forEach((btn) => {
      // Assign data-answer if missing — infer from leading A)/B)/C)/D) or index
      if (!btn.dataset.answer) {
        const match = btn.textContent.trim().match(/^([A-D])\)/);
        if (match) {
          btn.dataset.answer = match[1];
        } else {
          const idx = buttons.indexOf(btn);
          btn.dataset.answer = String.fromCharCode(65 + idx);
        }
      }

      // Skip buttons that already carry an inline onclick to avoid double-fire
      if (btn.hasAttribute('onclick')) return;

      btn.addEventListener('click', () => {
        choose(btn, correctLabel);
      });
    });
  });
});
