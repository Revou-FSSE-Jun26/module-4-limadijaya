"use client";

import { useEffect, useId, useState } from "react";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";

export interface CardSearchInputProps {
  onTermChange: (term: string) => void;
}

/** Client-side title filter. The raw text is debounced 300 ms and no request is sent (FRONT-008). */
export default function CardSearchInput({ onTermChange }: CardSearchInputProps) {
  const id = useId();
  const [text, setText] = useState("");
  const term = useDebouncedValue(text, 300);
  useEffect(() => {
    onTermChange(term);
  }, [term, onTermChange]);
  return (
    <div>
      <label htmlFor={id} className="sr-only">
        Search cards
      </label>
      <input
        id={id}
        type="search"
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Search cards by title"
        className="min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-indigo-600 sm:w-72"
      />
    </div>
  );
}