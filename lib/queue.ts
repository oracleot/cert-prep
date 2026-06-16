import { Queue, Worker, QueueEvents } from "bullmq";

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";
const LANGGRAPH_URL = process.env.LANGGRAPH_URL || "http://localhost:8000";
const WORKER_VERSION = "phase3-jobs-v1";

function getConnectionOptions() {
  const url = new URL(REDIS_URL);
  const isTls = url.protocol === "rediss:";
  const db = url.pathname ? Number.parseInt(url.pathname.slice(1) || "0", 10) : 0;

  return {
    host: url.hostname,
    port: Number.parseInt(url.port || "6379", 10),
    db: Number.isNaN(db) ? 0 : db,
    username: url.username || undefined,
    password: url.password || undefined,
    maxRetriesPerRequest: null,
    ...(isTls ? { tls: {} } : {}),
  };
}

const connection = getConnectionOptions();

async function runBackendJob(path: string, onboardingId: string) {
  const res = await fetch(`${LANGGRAPH_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ onboarding_id: onboardingId }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Backend job ${path} failed: ${body}`);
  }

  return res.json();
}

// Prevent multiple instances in development due to hot reloading
const globalForBullMQ = global as unknown as {
  __worker?: Worker;
  __workerVersion?: string;
  __queue?: Queue;
  __queueEvents?: QueueEvents;
};

if (
  process.env.NODE_ENV !== "production" &&
  globalForBullMQ.__worker &&
  globalForBullMQ.__workerVersion !== WORKER_VERSION
) {
  void globalForBullMQ.__worker.close();
  globalForBullMQ.__worker = undefined;
}

export const agentQueue =
  globalForBullMQ.__queue || new Queue("agent-tasks", { connection });

export const agentWorker =
  globalForBullMQ.__worker ||
  new Worker(
    "agent-tasks",
    async (job) => {
      console.log(`[JobQueue] Processing job ${job.id} of type ${job.name}`);
      if (job.name === "blueprint_scout") {
        await runBackendJob("/jobs/blueprint-scout", job.data.onboardingId);
        await agentQueue.add(
          "curriculum_builder",
          { onboardingId: job.data.onboardingId },
          { jobId: `curriculum-${job.data.onboardingId}` },
        );
      } else if (job.name === "curriculum_builder") {
        await runBackendJob("/jobs/curriculum-builder", job.data.onboardingId);
      }
    },
    { connection, autorun: true },
  );

export const agentQueueEvents =
  globalForBullMQ.__queueEvents || new QueueEvents("agent-tasks", { connection });

if (process.env.NODE_ENV !== "production") {
  globalForBullMQ.__queue = agentQueue;
  globalForBullMQ.__worker = agentWorker;
  globalForBullMQ.__workerVersion = WORKER_VERSION;
  globalForBullMQ.__queueEvents = agentQueueEvents;
}

agentWorker.on("ready", () => {
  console.log('[JobQueue] Worker is ready and listening for jobs on "agent-tasks"');
});

agentWorker.on("failed", (job, err) => {
  console.error(`[JobQueue] Job ${job?.id} failed:`, err);
});

agentWorker.on("completed", (job) => {
  console.log(`[JobQueue] Job ${job.id} completed successfully`);
});

agentQueue.client.then((client) => {
  client.on("connect", () => {
    console.log("[JobQueue] Successfully connected to Redis");
  });
  client.on("error", (err) => {
    console.error("[JobQueue] Redis connection error:", err);
  });
});
