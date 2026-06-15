import type { DashboardMetrics } from '../types';

const API_BASE = '/api/v1';

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

async function ensureCsrf(): Promise<void> {
  if (getCsrfToken()) return;
  await fetch(`${API_BASE}/csrf/`, { credentials: 'include' });
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const method = (options.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    await ensureCsrf();
  }

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (method !== 'GET' && method !== 'HEAD') {
    headers['Content-Type'] = 'application/json';
    headers['X-CSRFToken'] = getCsrfToken();
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data as { error?: string }).error || `Error ${res.status}`);
  }
  return data as T;
}

export const api = {
  metrics: (country: 'all' | 'AR' | 'CL' = 'all') =>
    request<DashboardMetricsResponse>(
      country === 'all' ? '/metrics/' : `/metrics/?country=${country}`
    ),
  sites: (country?: 'AR' | 'CL') =>
    request<{ providers: ProviderResponse[] }>(
      country ? `/sites/?country=${country}` : '/sites/'
    ),
  createSite: (body: SitePayload) =>
    request<{ provider: ProviderResponse }>('/sites/create/', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateSite: (slug: string, body: Partial<SitePayload>) =>
    request<{ provider: ProviderResponse }>(`/sites/${slug}/`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),
  deleteSite: (slug: string) =>
    request<{ ok: boolean }>(`/sites/${slug}/delete/`, { method: 'DELETE' }),
  products: (params?: Record<string, string>) => {
    const q = params ? `?${new URLSearchParams(params)}` : '';
    return request<{ products: ProductResponse[]; providers: string[] }>(`/products/${q}`);
  },
  scrape: (body: ScrapePayload = {}) =>
    request<{ jobId: number; status: string }>('/scrape/', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  stopScrape: (jobId?: number) =>
    request<{ jobId: number; status: string }>('/scrape/stop/', {
      method: 'POST',
      body: JSON.stringify(jobId ? { jobId } : {}),
    }),
  exportReadiness: () => request<ExportReadinessResponse>('/export/readiness/'),
  export: (body: { format?: string } = {}) =>
    request<{ jobId: number; status: string }>('/export/', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  jobStatus: (jobId?: number) => {
    const q = jobId ? `?jobId=${jobId}` : '';
    return request<JobStatusResponse>(`/job/${q}`);
  },
  exportsList: () => request<{ exports: ExportFile[] }>('/exports/'),
  exportDownloadUrl: (fileName: string) =>
    `${API_BASE}/exports/download/?name=${encodeURIComponent(fileName)}`,
};

export function downloadExportFile(fileName: string) {
  const a = document.createElement('a');
  a.href = api.exportDownloadUrl(fileName);
  a.download = fileName;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export interface CountryMetricsBlock {
  country: string;
  currency: string;
  totalProducts: number;
  activeProviders: number;
  avgPrice: number;
  lastUpdate: string | null;
  priceChanges24h: number;
  hasData?: boolean;
  charts: DashboardMetrics['charts'];
}

export interface DashboardMetricsResponse {
  country: string;
  currency: string;
  totalProducts: number;
  activeProviders: number;
  avgPrice: number;
  lastUpdate: string | null;
  priceChanges24h: number;
  hasData?: boolean;
  charts: DashboardMetrics['charts'] & {
    countryCompare?: {
      country: string;
      label: string;
      productos: number;
      proveedores: number;
      precioPromedio: number;
    }[];
  };
  byCountry?: {
    AR: CountryMetricsBlock;
    CL: CountryMetricsBlock;
  };
}

export interface ProviderResponse {
  id: string;
  slug: string;
  name: string;
  country: 'AR' | 'CL';
  baseUrl: string;
  catalogUrls: string[];
  isActive: boolean;
  scraper?: string;
  currency?: string;
  lastScrape?: string;
  productsCount: number;
}

export interface ProductResponse {
  id: string;
  name: string;
  category: string;
  provider: string;
  price: number | null;
  priceDisplay?: string | null;
  priceList?: number | null;
  priceListDisplay?: string | null;
  discountPercent?: number | null;
  discountDisplay?: string | null;
  priceWithoutTax?: number | null;
  priceWithoutTaxDisplay?: string | null;
  priceTransfer?: number | null;
  priceTransferDisplay?: string | null;
  currency: string;
  verifyUrl?: string;
  urlTrust?: string;
  urlTrustLabel?: string;
  safeToOpen?: boolean;
  availability: string;
  url: string;
  imageUrl?: string;
  lastUpdated: string;
  priceHistory: { date: string; price: number }[];
}

export interface SitePayload {
  name: string;
  country: 'AR' | 'CL';
  baseUrl: string;
  catalogUrls: string[];
  isActive: boolean;
  scraper?: string;
  currency?: string;
}

export interface ScrapePayload {
  siteSlug?: string;
  country?: string;
  maxPages?: number;
  maxProducts?: number;
  doExport?: boolean;
  exportFormat?: string;
}

export interface JobProgressMeta {
  message?: string;
  currentSite?: string;
  siteIndex?: number;
  totalSites?: number;
  phase?: string;
  productsDone?: number;
  productsTotal?: number;
}

export interface ExportFileInfo {
  key: string;
  name: string;
  downloadUrl: string;
}

export interface JobStatusResponse {
  jobId?: number;
  jobType?: string;
  running: boolean;
  status: string;
  log: string;
  error: string;
  progress: number;
  progressMessage?: string;
  progressMeta?: JobProgressMeta;
  etaSeconds?: number | null;
  productsInDb?: number;
  productsForJob?: number;
  exportFiles?: ExportFileInfo[];
  result?: { export_paths?: Record<string, string>; scrapeRunId?: string };
}

export interface ExportFile {
  name: string;
  size: number;
  modified: number;
  downloadUrl?: string;
}

export interface ExportReadinessResponse {
  canExport: boolean;
  totalProducts: number;
  exportableProducts: number;
  scrapingRunning: boolean;
  jobRunning: boolean;
  lastScrapeStatus: string | null;
  lastScrapeAt: string | null;
  message: string;
  securityNote?: string;
  blockedUrls?: number;
  unverifiedUrls?: number;
}
