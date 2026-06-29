/**
 * Client-side quiz hydrator.
 *
 * Attaches click handlers to every <section class="quiz"> on the page.
 * Single-select (default): click a choice to grade instantly.
 * Multi-select (data-multi): click toggles selection; grading happens
 *   automatically once the learner has picked data-answers choices.
 *
 * Writes only data-* attributes and class hooks — the existing
 * assets/course.css owns all visual styles.
 */
(function () {
  "use strict";

  var EXPLANATION_SELECTOR = "aside.explanation";
  var CHOICE_SELECTOR = "button.choice";

  function revealExplanation(section) {
    var explanation = section.querySelector(EXPLANATION_SELECTOR);
    if (!explanation) return;
    explanation.classList.add("is-revealed");
    explanation.setAttribute("aria-live", "polite");
  }

  function lockSection(section) {
    section.setAttribute("data-locked", "true");
    var buttons = section.querySelectorAll(CHOICE_SELECTOR);
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].disabled = true;
    }
  }

  function gradeSingleSelect(section, clicked) {
    var buttons = section.querySelectorAll(CHOICE_SELECTOR);
    var correctBtn = null;
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].hasAttribute("data-correct")) {
        correctBtn = buttons[i];
        break;
      }
    }

    if (clicked.hasAttribute("data-correct")) {
      clicked.setAttribute("data-result", "correct");
    } else {
      clicked.setAttribute("data-result", "incorrect");
      if (correctBtn && correctBtn !== clicked) {
        correctBtn.setAttribute("data-result", "correct");
      }
    }

    lockSection(section);
    revealExplanation(section);
  }

  function isSelected(button) {
    return button.getAttribute("data-selected") === "true";
  }

  function toggleMultiSelect(button) {
    var section = button.closest("section.quiz");
    if (!section || section.getAttribute("data-locked") === "true") return;

    var expected = parseInt(section.getAttribute("data-answers"), 10);
    if (isNaN(expected) || expected < 1) expected = 2;

    if (isSelected(button)) {
      button.setAttribute("data-selected", "false");
      button.setAttribute("aria-checked", "false");
      return;
    }

    var buttons = section.querySelectorAll(CHOICE_SELECTOR);
    var currentCount = 0;
    for (var i = 0; i < buttons.length; i++) {
      if (isSelected(buttons[i])) currentCount++;
    }

    if (currentCount >= expected) return; // ignore overflow clicks

    button.setAttribute("data-selected", "true");
    button.setAttribute("aria-checked", "true");

    var newCount = currentCount + 1;
    if (newCount === expected) {
      gradeMultiSelect(section);
    }
  }

  function gradeMultiSelect(section) {
    var buttons = section.querySelectorAll(CHOICE_SELECTOR);
    var correctSet = [];
    var selectedSet = [];
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].hasAttribute("data-correct")) {
        correctSet.push(buttons[i]);
      }
      if (isSelected(buttons[i])) {
        selectedSet.push(buttons[i]);
      }
    }

    var allMatch = correctSet.length === selectedSet.length;
    if (allMatch) {
      for (var j = 0; j < correctSet.length; j++) {
        var inSelected = false;
        for (var k = 0; k < selectedSet.length; k++) {
          if (selectedSet[k] === correctSet[j]) { inSelected = true; break; }
        }
        if (!inSelected) { allMatch = false; break; }
      }
    }

    for (var s = 0; s < selectedSet.length; s++) {
      var btn = selectedSet[s];
      var isCorrectChoice = btn.hasAttribute("data-correct");
      if (allMatch && isCorrectChoice) {
        btn.setAttribute("data-result", "correct");
      } else {
        btn.setAttribute("data-result", "incorrect");
      }
    }

    if (!allMatch) {
      for (var u = 0; u < correctSet.length; u++) {
        var wasSelected = false;
        for (var v = 0; v < selectedSet.length; v++) {
          if (selectedSet[v] === correctSet[u]) { wasSelected = true; break; }
        }
        if (!wasSelected) {
          correctSet[u].setAttribute("data-result", "correct");
        }
      }
    }

    lockSection(section);
    revealExplanation(section);
  }

  function initMultiSelect(section) {
    var buttons = section.querySelectorAll(CHOICE_SELECTOR);
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute("role", "checkbox");
      buttons[i].setAttribute("aria-checked", "false");
      buttons[i].addEventListener("click", function (event) {
        toggleMultiSelect(event.currentTarget);
      });
    }
  }

  function initSingleSelect(section) {
    var buttons = section.querySelectorAll(CHOICE_SELECTOR);
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", function (event) {
        var target = event.currentTarget;
        var sec = target.closest("section.quiz");
        if (sec && sec.getAttribute("data-locked") !== "true") {
          gradeSingleSelect(sec, target);
        }
      });
    }
  }

  function initQuiz(section) {
    if (section.getAttribute("data-multi") !== null) {
      initMultiSelect(section);
    } else {
      initSingleSelect(section);
    }
  }

  function init() {
    var sections = document.querySelectorAll("section.quiz");
    for (var i = 0; i < sections.length; i++) {
      initQuiz(sections[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();