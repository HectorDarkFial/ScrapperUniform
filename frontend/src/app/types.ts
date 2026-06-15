export interface Product {
  id: string;
  name: string;
  category: 'scrubs' | 'lab-coats' | 'shoes' | 'accessories';
  provider: string;
  stockText?: string | null;
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
  currency: 'ARS' | 'CLP' | string;
  verifyUrl?: string;
  urlTrust?: 'trusted' | 'unverified' | 'blocked';
  urlTrustLabel?: string;
  safeToOpen?: boolean;
  availability: 'in-stock' | 'low-stock' | 'out-of-stock';
  url: string;
  imageUrl?: string;
  lastUpdated: string;
  priceHistory: { date: string; price: number }[];
}

export interface Provider {
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

export interface DashboardMetrics {
  totalProducts: number;
  activeProviders: number;
  avgPrice: number;
  lastUpdate: string | null;
  priceChanges24h: number;
  charts: {
    categoryData: { name: string; value: number }[];
    providerData: { name: string; productos: number; country?: string }[];
    priceData: { name: string; precio: number; currency?: string }[];
    priceHistoryData: { fecha: string; promedio: number }[];
    countryCompare?: {
      country: string;
      label: string;
      productos: number;
      proveedores: number;
      precioPromedio: number;
    }[];
  };
}
