/**
 * Quiz Hydrator — vanilla JS in public/quiz-hydrator.js. Tests evaluate
 * the script inside a hand-rolled DOM mock so we avoid jsdom (the
 * project's vitest config runs with environment: "node"). The mock
 * supports just enough of the DOM API the hydrator actually touches.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

type Handler = (e: { currentTarget: MockEl }) => void;

class MockEl {
  tag: string;
  classes = new Set<string>();
  attrs: Record<string, string> = {};
  children: MockEl[] = [];
  parent: MockEl | null = null;
  listeners: Record<string, Handler[]> = {};
  disabled = false;

  constructor(tag: string, classes: string[] = []) {
    this.tag = tag.toLowerCase();
    for (const c of classes) this.classes.add(c);
  }

  matches(sel: string) {
    const m = sel.trim().match(/^([a-z]+)?(?:\.([\w-]+))?$/i);
    if (!m) return false;
    const [, t, c] = m;
    return (!t || this.tag === t.toLowerCase()) && (!c || this.classes.has(c));
  }

  querySelectorAll(sel: string): MockEl[] {
    const out: MockEl[] = [];
    const walk = (e: MockEl) => {
      for (const c of e.children) {
        if (c.matches(sel)) out.push(c);
        walk(c);
      }
    };
    walk(this);
    return out;
  }

  querySelector(sel: string) { return this.querySelectorAll(sel)[0] ?? null; }

  closest(sel: string) {
    let cur: MockEl | null = this;
    while (cur) {
      if (cur.matches(sel)) return cur;
      cur = cur.parent;
    }
    return null;
  }

  hasAttribute(n: string) { return n in this.attrs; }
  getAttribute(n: string) { return this.attrs[n] ?? null; }
  setAttribute(n: string, v: string) { this.attrs[n] = String(v); }
  removeAttribute(n: string) { delete this.attrs[n]; }
  addEventListener(ev: string, h: Handler) { (this.listeners[ev] ??= []).push(h); }
  classList = { add: (c: string) => this.classes.add(c) };
  click() { for (const h of this.listeners["click"] ?? []) h({ currentTarget: this }); }
}

function makeEnv() {
  const html = new MockEl("html");
  const body = new MockEl("body");
  html.children.push(body);
  body.parent = html;
  const domHandlers: Record<string, Handler[]> = {};
  (html as unknown as { addEventListener: (e: string, h: Handler) => void }).addEventListener =
    (e, h) => ((domHandlers[e] ??= []).push(h));
  (html as unknown as { readyState: string }).readyState = "loading";
  const doc = html as unknown as MockEl;
  return {
    doc,
    fireDCL() { for (const h of domHandlers["DOMContentLoaded"] ?? []) h({ currentTarget: doc }); },
  };
}

function loadHydrator(env: ReturnType<typeof makeEnv>) {
  const src = readFileSync(resolve(process.cwd(), "public/quiz-hydrator.js"), "utf8");
  new Function("document", "window", src)(env.doc as unknown as Document, undefined);
}

function makeSection(
  env: ReturnType<typeof makeEnv>,
  opts: { multi?: boolean; answers?: number; correctIdx?: number[] } = {},
) {
  const sec = new MockEl("section", ["quiz"]);
  if (opts.multi) sec.setAttribute("data-multi", "");
  if (opts.answers) sec.setAttribute("data-answers", String(opts.answers));
  const buttons: MockEl[] = [];
  for (let i = 0; i < 4; i++) {
    const b = new MockEl("button", ["choice"]);
    if (opts.correctIdx?.includes(i)) b.setAttribute("data-correct", "");
    sec.children.push(b);
    b.parent = sec;
    buttons.push(b);
  }
  const aside = new MockEl("aside", ["explanation"]);
  sec.children.push(aside);
  aside.parent = sec;
  env.doc.children[0].children.push(sec);
  sec.parent = env.doc.children[0];
  return { sec, buttons, aside };
}

describe("quiz-hydrator — single-select", () => {
  it("surfaces the correct answer when the learner picks wrong", () => {
    const env = makeEnv();
    const { sec, buttons, aside } = makeSection(env, { correctIdx: [0] });
    loadHydrator(env);
    env.fireDCL();
    buttons[1].click();
    expect(buttons[1].getAttribute("data-result")).toBe("incorrect");
    expect(buttons[0].getAttribute("data-result")).toBe("correct");
    expect(sec.getAttribute("data-locked")).toBe("true");
    expect(aside.classes.has("is-revealed")).toBe(true);
    expect(aside.getAttribute("aria-live")).toBe("polite");
    expect(buttons[0].disabled).toBe(true);
  });

  it("marks the click correct and locks the section", () => {
    const env = makeEnv();
    const { sec, buttons } = makeSection(env, { correctIdx: [2] });
    loadHydrator(env);
    env.fireDCL();
    buttons[2].click();
    expect(buttons[2].getAttribute("data-result")).toBe("correct");
    expect(sec.getAttribute("data-locked")).toBe("true");
    for (const b of buttons) expect(b.disabled).toBe(true);
  });
});

describe("quiz-hydrator — multi-select", () => {
  it("toggles aria-checked without grading until count met", () => {
    const env = makeEnv();
    const { buttons } = makeSection(env, { multi: true, answers: 2, correctIdx: [0, 1] });
    loadHydrator(env);
    env.fireDCL();
    const [c1, , w1] = buttons;
    expect(c1.getAttribute("role")).toBe("checkbox");
    expect(c1.getAttribute("aria-checked")).toBe("false");
    c1.click();
    expect(c1.getAttribute("aria-checked")).toBe("true");
    expect(c1.getAttribute("data-selected")).toBe("true");
    expect(w1.getAttribute("data-selected")).toBeNull();
  });

  it("grades correct when the right set is selected", () => {
    const env = makeEnv();
    const { sec, buttons } = makeSection(env, { multi: true, answers: 2, correctIdx: [0, 2] });
    loadHydrator(env);
    env.fireDCL();
    buttons[0].click();
    buttons[2].click();
    expect(buttons[0].getAttribute("data-result")).toBe("correct");
    expect(buttons[2].getAttribute("data-result")).toBe("correct");
    expect(sec.getAttribute("data-locked")).toBe("true");
  });

  it("grades incorrect and surfaces unselected correct buttons", () => {
    const env = makeEnv();
    const { sec, buttons } = makeSection(env, { multi: true, answers: 2, correctIdx: [0, 1] });
    loadHydrator(env);
    env.fireDCL();
    buttons[0].click();
    buttons[3].click();
    expect(buttons[0].getAttribute("data-result")).toBe("incorrect");
    expect(buttons[3].getAttribute("data-result")).toBe("incorrect");
    expect(buttons[1].getAttribute("data-result")).toBe("correct");
    expect(sec.getAttribute("data-locked")).toBe("true");
  });

  it("ignores clicks beyond expected count (overflow)", () => {
    const env = makeEnv();
    const { buttons } = makeSection(env, { multi: true, answers: 2, correctIdx: [0, 1] });
    loadHydrator(env);
    env.fireDCL();
    buttons[0].click();
    buttons[1].click();
    buttons[3].click();
    expect(buttons[3].getAttribute("data-selected")).toBeNull();
    expect(buttons[3].getAttribute("data-result")).toBeNull();
  });
});