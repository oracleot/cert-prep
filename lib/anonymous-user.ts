const USER_ID_KEY = "gauntlet.anonymous-user-id";

export function getAnonymousUserId() {
  if (typeof window === "undefined") return "";

  const existing = window.localStorage.getItem(USER_ID_KEY);
  if (existing) return existing;

  const id = crypto.randomUUID();
  window.localStorage.setItem(USER_ID_KEY, id);
  return id;
}
