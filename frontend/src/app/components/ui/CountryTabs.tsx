import { ToggleButton, ToggleButtonGroup, Box } from '@mui/material';

export type CountryFilter = 'all' | 'AR' | 'CL';

export const DEFAULT_COUNTRY: CountryFilter = 'CL';

export const CL_COLOR = '#1976d2';
export const AR_COLOR = '#ed6c02';

const ORDER: CountryFilter[] = ['CL', 'AR', 'all'];

const LABELS: Record<CountryFilter, string> = {
  CL: '🇨🇱 Chile',
  AR: '🇦🇷 Argentina',
  all: 'Todos los países',
};

interface CountryTabsProps {
  value: CountryFilter;
  onChange: (value: CountryFilter) => void;
  size?: 'small' | 'medium';
}

export function CountryTabs({ value, onChange, size = 'medium' }: CountryTabsProps) {
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}>
      <ToggleButtonGroup
        value={value}
        exclusive
        onChange={(_, v: CountryFilter | null) => v && onChange(v)}
        size={size}
        aria-label="filtrar por país"
      >
        {ORDER.map((code) => (
          <ToggleButton key={code} value={code}>
            {LABELS[code]}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
    </Box>
  );
}

export function countrySubtitle(country: CountryFilter): string {
  if (country === 'CL') return 'Chile · precios en CLP (peso chileno)';
  if (country === 'AR') return 'Argentina · precios en ARS (peso argentino)';
  return 'Comparativa: Chile (CLP) y Argentina (ARS). Clic en un gráfico para filtrar.';
}

export function countryLabel(country: CountryFilter): string {
  if (country === 'CL') return 'Chile';
  if (country === 'AR') return 'Argentina';
  return 'Todos';
}

export function currencyForCountry(country: CountryFilter): string {
  if (country === 'CL') return 'CLP';
  if (country === 'AR') return 'ARS';
  return '';
}

export function formatMoney(amount: number, country: CountryFilter, currency?: string): string {
  if (amount <= 0) return '—';
  const cur = currency || currencyForCountry(country);
  const locale = country === 'CL' ? 'es-CL' : 'es-AR';
  const formatted = amount.toLocaleString(locale, { maximumFractionDigits: 0 });
  return cur ? `${cur} ${formatted}` : formatted;
}

export function formatMoneyByCode(
  amount: number,
  countryCode?: string,
  currency?: string
): string {
  const c = countryCode === 'CL' || countryCode === 'AR' ? countryCode : 'all';
  return formatMoney(amount, c as CountryFilter, currency);
}
