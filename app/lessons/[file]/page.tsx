import { notFound } from "next/navigation";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { AppNav } from "@/components/navigation/app-nav";

type Params = { file: string };

export async function generateMetadata({ params }: { params: Promise<Params> }) {
  const { file } = await params;
  const slug = file.replace(/^\d{4}-/, "").replace(/\.html$/, "");
  const title = slug
    .split("-")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
  return { title: `${title} · Lesson` };
}

function stripScriptTags(html: string): string {
  return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "");
}

function sanitizeFile(file: string): string | null {
  if (!/^\d{4}-[\w-]+\.html$/.test(file)) return null;
  return file;
}

export default async function LessonPage({ params }: { params: Promise<Params> }) {
  const { file } = await params;
  const safe = sanitizeFile(file);
  if (!safe) notFound();
  const path = join(process.cwd(), "public", "lessons", safe);
  let raw: string;
  try {
    raw = await readFile(path, "utf8");
  } catch {
    notFound();
  }
  const body = stripScriptTags(raw);
  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppNav />
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <a
          href="/lessons"
          className="mb-4 inline-block text-sm font-bold text-amber-700 hover:underline dark:text-amber-300"
        >
          ← All lessons
        </a>
        <div dangerouslySetInnerHTML={{ __html: body }} />
        <script src="/quiz-hydrator.js" defer></script>
      </div>
    </div>
  );
}