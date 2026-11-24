"use client";

import { useEffect, useState } from "react";

/** Returns `value` after it has stayed unchanged for `delayMs`. The timer is cleared on unmount (FE-16). */
export function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}