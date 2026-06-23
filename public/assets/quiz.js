/**
 * Quiz interaction — legacy choose() plus enhanced walkthrough reveal.
 * Walkthrough mode (data-walkthrough="true"): rationale, explanation, and
 * knowledge-gap asides are hidden until the user selects an answer, then
 * revealed inline so the stem and all options remain visible.
 */
function choose(button, expected) {
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
  const selector =
    'section[data-quiz][data-walkthrough="true"] aside[data-rationale-for], ' +
    'section[data-quiz][data-walkthrough="true"] aside.explanation, ' +
    'section[data-quiz][data-walkthrough="true"] aside.knowledge-gap';
  document.querySelectorAll(selector).forEach((aside) => {
    aside.hidden = true;
  });
});
