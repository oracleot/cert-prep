import { readdir } from "node:fs/promises";
import Link from "next/link";

import { AppNav } from "@/components/navigation/app-nav";

type Lesson = {
  file: string;
  number: number;
  title: string;
  domain: string;
};

const DOMAIN_LABELS = [
  { label: "Domain 1", min: 1, max: 13 },
  { label: "Domain 2", min: 14, max: 18 },
  { label: "Domain 3", min: 19, max: 23 },
];

function titleFromFile(file: string) {
  const slug = file.replace(/^\d{4}-/, "").replace(/\.html$/, "");
  return slug.split("-").map((word) => word[0].toUpperCase() + word.slice(1)).join(" ");
}

function domainFor(number: number) {
  return DOMAIN_LABELS.find((domain) => number >= domain.min && number <= domain.max)?.label ?? "Other";
}

async function loadLessons(): Promise<Lesson[]> {
  const files = await readdir(`${process.cwd()}/lessons`);
  return files
    .filter((file) => /^\d{4}-.+\.html$/.test(file))
    .map((file) => {
      const number = Number(file.slice(0, 4));
      return { file, number, title: titleFromFile(file), domain: domainFor(number) };
    })
    .sort((a, b) => a.number - b.number);
}

export default async function LessonsPage() {
  const lessons = await loadLessons();
  const domains = [...new Set(lessons.map((lesson) => lesson.domain))];

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <AppNav />
        <section className="mt-8 rounded-[2rem] border border-zinc-200 bg-white p-7 dark:border-zinc-800 dark:bg-zinc-950 sm:p-10">
          <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
            Lessons
          </p>
          <h1 className="mt-4 text-4xl font-black tracking-tight">Study the blueprint between Rex rounds.</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-500 dark:text-zinc-400">
            Use these quick lessons when Sage exposes a gap, then come back to the gauntlet.
          </p>
        </section>
        <section className="mt-5 grid gap-5 lg:grid-cols-3">
          {domains.map((domain) => (
            <div key={domain} className="rounded-[2rem] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
              <h2 className="font-black text-zinc-950 dark:text-zinc-50">{domain}</h2>
              <div className="mt-4 space-y-2">
                {lessons.filter((lesson) => lesson.domain === domain).map((lesson) => (
                  <Link
                    key={lesson.file}
                    href={`/lessons/${lesson.file.replace(/\.html$/, "")}`}
                    className="block rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-bold text-zinc-700 hover:border-amber-300 hover:bg-amber-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:border-amber-300/70 dark:hover:bg-amber-300/10"
                  >
                    {String(lesson.number).padStart(4, "0")} · {lesson.title}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </section>
      </div>
    </main>
  );
}
