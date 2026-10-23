import { AlertTriangle } from 'lucide-react';

function retryCopy(seconds) {
  if (seconds === 0) return 'You can try again now.';
  if (seconds < 60) return `You can try again in about ${seconds} second${seconds === 1 ? '' : 's'}.`;
  const minutes = Math.ceil(seconds / 60);
  return `You can try again in about ${minutes} minute${minutes === 1 ? '' : 's'}.`;
}

export function RateLimitBanner({ rateLimit }) {
  if (!rateLimit) return null;

  const message = rateLimit.service === 'stt'
    ? 'Voice transcription limit reached.'
    : 'AI request limit reached.';
  const retryMessage = Number.isInteger(rateLimit.retry_after_seconds)
    && rateLimit.retry_after_seconds >= 0
    ? retryCopy(rateLimit.retry_after_seconds)
    : 'The retry time is unknown. Please try again later.';

  return (
    <div
      role="alert"
      className="mb-3 flex items-start gap-3 rounded-xl border border-amber-300/20 bg-amber-300/[0.07] px-4 py-3 text-sm text-amber-100"
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
      <p>
        <span className="font-medium">{message}</span>{' '}
        <span className="text-amber-100/75">{retryMessage}</span>
      </p>
    </div>
  );
}
