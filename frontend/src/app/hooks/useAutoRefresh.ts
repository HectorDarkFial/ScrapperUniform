import { useCallback, useEffect, useRef, useState } from 'react';
import { useScrapeJob } from '../context/ScrapeJobContext';

const IDLE_MS = 20_000;
const SCRAPING_MS = 3_000;

export function useAutoRefresh<T>(loader: () => Promise<T>, deps: unknown[] = []) {
  const { refreshTick, job } = useScrapeJob();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
  const mounted = useRef(true);

  const load = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true);
      else setRefreshing(true);
      setError('');
      try {
        const result = await loader();
        if (mounted.current) {
          setData(result);
          setLastRefreshedAt(new Date());
        }
      } catch (e) {
        if (mounted.current) setError(String(e));
      } finally {
        if (mounted.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    deps
  );

  useEffect(() => {
    mounted.current = true;
    load();
    return () => {
      mounted.current = false;
    };
  }, [load, refreshTick]);

  useEffect(() => {
    const ms = job?.running ? SCRAPING_MS : IDLE_MS;
    const id = setInterval(() => load(true), ms);
    return () => clearInterval(id);
  }, [job?.running, load]);

  const reload = useCallback(() => load(true), [load]);

  const refreshIntervalSec = job?.running ? SCRAPING_MS / 1000 : IDLE_MS / 1000;

  return {
    data,
    error,
    loading,
    refreshing,
    reload,
    lastRefreshedAt,
    refreshIntervalSec,
    isScrapeActive: Boolean(job?.running),
  };
}
