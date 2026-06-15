import { Box, Typography, Chip } from '@mui/material';
import {
  type CountryFilter,
  countryLabel,
  currencyForCountry,
  CL_COLOR,
  AR_COLOR,
} from './CountryTabs';

interface CurrencyBannerProps {
  country: CountryFilter;
  onSelectCountry?: (c: CountryFilter) => void;
}

export function CurrencyBanner({ country, onSelectCountry }: CurrencyBannerProps) {
  if (country === 'all') {
    return (
      <Box
        sx={{
          mb: 2,
          p: 1.5,
          borderRadius: 2,
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 1,
          alignItems: 'center',
        }}
      >
        <Typography variant="body2" color="text.secondary">
          Clic en Chile o Argentina en los gráficos para ver precios en moneda local:
        </Typography>
        <Chip
          label="Chile · CLP"
          onClick={() => onSelectCountry?.('CL')}
          sx={{ bgcolor: CL_COLOR, color: '#fff', fontWeight: 600 }}
        />
        <Chip
          label="Argentina · ARS"
          onClick={() => onSelectCountry?.('AR')}
          sx={{ bgcolor: AR_COLOR, color: '#fff', fontWeight: 600 }}
        />
      </Box>
    );
  }

  const color = country === 'CL' ? CL_COLOR : AR_COLOR;
  const cur = currencyForCountry(country);

  return (
    <Box
      sx={{
        mb: 2,
        p: 1.5,
        borderRadius: 2,
        bgcolor: color,
        color: '#fff',
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        flexWrap: 'wrap',
      }}
    >
      <Typography variant="subtitle1" fontWeight={700}>
        {countryLabel(country)}
      </Typography>
      <Typography variant="body2" sx={{ opacity: 0.95 }}>
        Todos los precios del panel se muestran en <strong>{cur}</strong>
      </Typography>
    </Box>
  );
}
