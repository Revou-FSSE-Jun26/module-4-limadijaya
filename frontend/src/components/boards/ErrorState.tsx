export interface ErrorStateProps {
  message: string;
}

/** Inline error for Server Components. Shows the API `error` text (FRONT-005-AC05). */
export default function ErrorState({ message }: ErrorStateProps) {
  return (
    <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <p className="font-medium">Something went wrong</p>
      <p className="mt-1">{message}</p>
    </div>
  );
}