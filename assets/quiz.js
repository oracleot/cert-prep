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
}
