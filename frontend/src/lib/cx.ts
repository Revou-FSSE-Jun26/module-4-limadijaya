/** Joins class names, skipping falsy values (FE-10). */
export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}