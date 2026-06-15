import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { api, type JobStatusResponse } from '../api/client';

interface ScrapeJobContextValue {
  job: JobStatusResponse | null;
  refreshTick: number;
  triggerRefresh: () => void;
  watchJob: (jobId: number) => void;
}

const ScrapeJobContext = createContext<ScrapeJobContextValue | null>(null);

export function ScrapeJobProvider({ children }: { children: ReactNode }) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const watchedJobId = useRef<number | null>(null);
  const lastRefreshProgress = useRef(-1);
  const lastRefreshAt = useRef(0);

  const triggerRefresh = useCallback(() => {
    setRefreshTick((t) => t + 1);
  }, []);

  const maybeRefreshData = useCallback(
    (status: JobStatusResponse) => {
      const now = Date.now();
      const progressChanged = status.progress !== lastRefreshProgress.current;
      const intervalElapsed = now - lastRefreshAt.current >= 3000;
      if (progressChanged || intervalElapsed) {
        lastRefreshProgress.current = status.progress;
        lastRefreshAt.current = now;
        triggerRefresh();
      }
    },
    [triggerRefresh]
  );

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollOnce = useCallback(async () => {
    try {
      const status = await api.jobStatus(watchedJobId.current ?? undefined);
      setJob(status);
      if (status.running) {
        maybeRefreshData(status);
      } else {
        stopPolling();
        watchedJobId.current = null;
        triggerRefresh();
      }
    } catch {
      stopPolling();
    }
  }, [stopPolling, triggerRefresh, maybeRefreshData]);

  const watchJob = useCallback(
    (jobId: number) => {
      watchedJobId.current = jobId;
      stopPolling();
      pollOnce();
      pollRef.current = setInterval(pollOnce, 800);
    },
    [pollOnce, stopPolling]
  );

  useEffect(() => {
    api.jobStatus().then(setJob).catch(() => setJob(null));
    return () => stopPolling();
  }, [stopPolling]);

  return (
    <ScrapeJobContext.Provider value={{ job, refreshTick, triggerRefresh, watchJob }}>
      {children}
    </ScrapeJobContext.Provider>
  );
}

export function useScrapeJob() {
  const ctx = useContext(ScrapeJobContext);
  if (!ctx) throw new Error('useScrapeJob debe usarse dentro de ScrapeJobProvider');
  return ctx;
}
