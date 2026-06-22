import { Button } from "@/components/ui/button";

type Props = {
  isOpen: boolean;
  isReady: boolean;
  isResetting: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

export function ResetProgressDialog({ isOpen, isReady, isResetting, onClose, onConfirm }: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/70 px-4 backdrop-blur-sm" role="presentation">
      <section
        aria-modal="true"
        role="dialog"
        aria-labelledby="reset-progress-title"
        className="w-full max-w-md rounded-[2rem] border border-rose-300 bg-white p-6 shadow-2xl dark:border-rose-900 dark:bg-zinc-950"
      >
        <p className="text-xs font-black uppercase tracking-[0.35em] text-rose-700 dark:text-rose-300">Permanent action</p>
        <h2 id="reset-progress-title" className="mt-3 text-2xl font-black text-zinc-950 dark:text-zinc-50">
          Reset DVA-C02 progress?
        </h2>
        <p className="mt-4 text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
          This will permanently delete your DVA-C02 progress. This cannot be undone.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Button type="button" variant="outline" onClick={onClose} disabled={isResetting}>
            Cancel
          </Button>
          <Button type="button" variant="destructive" onClick={onConfirm} disabled={!isReady || isResetting}>
            {isResetting ? "Resetting..." : isReady ? "Confirm reset" : "Wait 3 seconds"}
          </Button>
        </div>
      </section>
    </div>
  );
}
