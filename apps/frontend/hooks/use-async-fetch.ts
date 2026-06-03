"use client";

import { useEffect, useRef, useState } from "react";

interface FetchState<T> {
  data: T | null;
  loading: boolean;   // true only on the very first fetch (no data yet)
  updating: boolean;  // true on subsequent fetches (data exists, refreshing)
  error: string | null;
}

export function useAsyncFetch<T>(
  fetcher: () => Promise<T>,
  deps: React.DependencyList,
): FetchState<T> {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    updating: false,
    error: null,
  });

  // Track whether we have data yet — use a ref so it's readable inside the effect
  // without creating a stale closure on `state`.
  const hasData = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const isFirstFetch = !hasData.current;
    setState((prev) => ({
      ...prev,
      loading: isFirstFetch,
      updating: !isFirstFetch,
      error: null,
    }));

    fetcher()
      .then((data) => {
        if (cancelled) return;
        hasData.current = true;
        setState({ data, loading: false, updating: false, error: null });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setState((prev) => ({
          ...prev,
          loading: false,
          updating: false,
          error: err instanceof Error ? err.message : "Failed to load data",
        }));
      });

    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
