const ONBOARDING_ID_KEY = "gauntlet.onboarding-id";

export function saveOnboardingId(onboardingId: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ONBOARDING_ID_KEY, onboardingId);
}

export function loadOnboardingId() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ONBOARDING_ID_KEY);
}
