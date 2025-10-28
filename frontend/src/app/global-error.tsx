"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <h2>Global Error Handler</h2>
        <p>{error.message}</p>
        <button onClick={reset}>Try again</button>
      </body>
    </html>
  );
}