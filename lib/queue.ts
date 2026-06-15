import { Queue, Worker, QueueEvents } from "bullmq";

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";

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

// Prevent multiple instances in development due to hot reloading
const globalForBullMQ = global as unknown as {
  __worker?: Worker;
  __queue?: Queue;
  __queueEvents?: QueueEvents;
};

export const agentQueue =
  globalForBullMQ.__queue || new Queue("agent-tasks", { connection });

export const agentWorker =
  globalForBullMQ.__worker ||
  new Worker(
    "agent-tasks",
    async (job) => {
      console.log(`[JobQueue] Processing job ${job.id} of type ${job.name}`);
      if (job.name === "blueprint_scout") {
        console.log("[JobQueue] Running blueprint_scout placeholder");
      } else if (job.name === "curriculum_builder") {
        console.log("[JobQueue] Running curriculum_builder placeholder");
      }
    },
    { connection, autorun: true },
  );

export const agentQueueEvents =
  globalForBullMQ.__queueEvents || new QueueEvents("agent-tasks", { connection });

if (process.env.NODE_ENV !== "production") {
  globalForBullMQ.__queue = agentQueue;
  globalForBullMQ.__worker = agentWorker;
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
