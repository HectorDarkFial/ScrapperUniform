import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Alert,
  ToggleButton,
  ToggleButtonGroup,
  Skeleton,
  Link,
} from '@mui/material';
import Grid from '@mui/material/GridLegacy';
import { CheckCircle, Warning, Cancel, OpenInNew, ViewModule, TableRows } from '@mui/icons-material';
import { api } from '../api/client';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { useScrapeJob } from '../context/ScrapeJobContext';
import { PageHeader } from './ui/PageHeader';
import { EmptyState } from './ui/EmptyState';
import {
  CountryTabs,
  countrySubtitle,
  DEFAULT_COUNTRY,
  formatMoneyByCode,
  type CountryFilter,
} from './ui/CountryTabs';
import type { Product } from '../types';

export function Products() {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('table');
  const [countryFilter, setCountryFilter] = useState<CountryFilter>(DEFAULT_COUNTRY);
  const [providerFilter, setProviderFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const { job } = useScrapeJob();

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(searchTerm.trim()), 400);
    return () => clearTimeout(t);
  }, [searchTerm]);

  const queryKey = useMemo(
    () => JSON.stringify({ q: debouncedSearch, provider: providerFilter, country: countryFilter }),
    [debouncedSearch, providerFilter, countryFilter]
  );

  useEffect(() => {
    setProviderFilter('all');
  }, [countryFilter]);

  const {
    data,
    error,
    loading,
    refreshing,
    reload,
    lastRefreshedAt,
    refreshIntervalSec,
    isScrapeActive,
  } = useAutoRefresh(async () => {
    const params: Record<string, string> = { limit: '300' };
    if (debouncedSearch) params.q = debouncedSearch;
    if (providerFilter !== 'all') params.provider = providerFilter;
    if (countryFilter !== 'all') params.country = countryFilter;
    return api.products(params);
  }, [queryKey]);

  const products = (data?.products ?? []) as Product[];
  const providers = data?.providers ?? [];

  const getAvailabilityColor = (availability: string) => {
    switch (availability) {
      case 'in-stock':
        return 'success';
      case 'low-stock':
        return 'warning';
      case 'out-of-stock':
        return 'error';
      default:
        return 'default';
    }
  };

  const getAvailabilityIcon = (availability: string) => {
    switch (availability) {
      case 'in-stock':
        return <CheckCircle fontSize="small" />;
      case 'low-stock':
        return <Warning fontSize="small" />;
      default:
        return <Cancel fontSize="small" />;
    }
  };

  const moneyCountry = (p: Product): CountryFilter | undefined => {
    if (countryFilter !== 'all') return countryFilter;
    if (p.currency === 'CLP') return 'CL';
    if (p.currency === 'ARS') return 'AR';
    return undefined;
  };

  const formatAmount = (p: Product, amount?: number | null) => {
    if (amount == null) return null;
    return formatMoneyByCode(amount, moneyCountry(p), p.currency);
  };

  const PriceBreakdown = ({ product }: { product: Product }) => (
    <Box>
      {product.priceList != null && (
        <Typography
          variant="caption"
          color="text.secondary"
          display="block"
          sx={{ textDecoration: 'line-through' }}
        >
          Original: {product.priceListDisplay || formatAmount(product, product.priceList)}
        </Typography>
      )}
      {product.discountDisplay && (
        <Chip
          size="small"
          color="error"
          label={
            product.discountPercent != null
              ? `${product.discountDisplay} (${product.discountPercent}%)`
              : product.discountDisplay
          }
          sx={{ height: 20, my: 0.25 }}
        />
      )}
      <Typography variant="body2" fontWeight={700}>
        {product.price != null
          ? product.priceDisplay || formatAmount(product, product.price)
          : '—'}
      </Typography>
      {product.priceWithoutTax != null && (
        <Typography variant="caption" color="text.secondary" display="block">
          Precio unitario:{' '}
          {product.priceWithoutTaxDisplay || formatAmount(product, product.priceWithoutTax)}
        </Typography>
      )}
      {product.priceTransfer != null && (
        <Typography variant="caption" color="text.secondary" display="block">
          Transferencia:{' '}
          {product.priceTransferDisplay || formatAmount(product, product.priceTransfer)}
        </Typography>
      )}
    </Box>
  );

  const verifyHref = (p: Product) => p.verifyUrl || p.url;

  const urlTrustColor = (trust?: string): 'success' | 'warning' | 'error' | 'default' => {
    if (trust === 'trusted') return 'success';
    if (trust === 'unverified') return 'warning';
    if (trust === 'blocked') return 'error';
    return 'default';
  };

  return (
    <Box>
      <PageHeader
        title="Productos"
        subtitle={countrySubtitle(countryFilter)}
        panelRefreshedAt={lastRefreshedAt}
        refreshIntervalSec={refreshIntervalSec}
        isLiveUpdating={isScrapeActive}
        onRefresh={reload}
        refreshing={refreshing}
        extra={
          <>
            <CountryTabs value={countryFilter} onChange={setCountryFilter} size="small" />
            {job?.running && (
              <Chip size="small" color="info" label="Actualizando tras scrape…" sx={{ ml: 1 }} />
            )}
          </>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'stretch', md: 'center' },
          gap: 2,
          mb: 2,
        }}
      >
        <Grid container spacing={2} sx={{ flex: 1 }}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              size="small"
              label="Buscar producto"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Proveedor</InputLabel>
              <Select
                value={providerFilter}
                label="Proveedor"
                onChange={(e) => setProviderFilter(e.target.value)}
              >
                <MenuItem value="all">Todos</MenuItem>
                {providers.map((p) => (
                  <MenuItem key={p} value={p}>
                    {p}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Typography variant="body2" color="text.secondary" sx={{ pt: 1 }}>
              {loading ? '…' : `${products.length} resultados`}
            </Typography>
          </Grid>
        </Grid>
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_, v) => v && setViewMode(v)}
          size="small"
        >
          <ToggleButton value="grid" aria-label="vista grilla">
            <ViewModule />
          </ToggleButton>
          <ToggleButton value="table" aria-label="vista tabla">
            <TableRows />
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {loading && products.length === 0 ? (
        <Skeleton variant="rounded" height={320} />
      ) : products.length === 0 ? (
        <EmptyState
          title="Sin productos para mostrar"
          description="Ejecutá un scraping en Proveedores. Esta vista se refresca sola cuando termina el trabajo."
        />
      ) : viewMode === 'grid' ? (
        <Grid container spacing={2}>
          {products.map((product) => (
            <Grid item xs={12} sm={6} lg={4} key={product.id}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom sx={{ lineHeight: 1.3 }}>
                    {product.name}
                  </Typography>
                  <Chip label={product.provider} size="small" sx={{ mb: 1 }} />
                  <PriceBreakdown product={product} />
                  <Chip
                    icon={getAvailabilityIcon(product.availability)}
                    label={product.availability}
                    color={getAvailabilityColor(product.availability)}
                    size="small"
                    sx={{ mt: 1 }}
                  />
                  {product.urlTrustLabel && (
                    <Chip
                      size="small"
                      label={product.urlTrustLabel}
                      color={urlTrustColor(product.urlTrust)}
                      sx={{ mt: 1 }}
                    />
                  )}
                  <Box mt={1}>
                    {product.safeToOpen ? (
                      <Link
                        href={verifyHref(product)}
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="caption"
                        sx={{ wordBreak: 'break-all' }}
                      >
                        Verificar precio en tienda
                      </Link>
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        URL no verificada — no se abre desde el panel
                      </Typography>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <TableContainer component={Paper} sx={{ maxHeight: { xs: '70vh', md: 'none' } }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Producto</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Proveedor</TableCell>
                <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Categoría</TableCell>
                <TableCell>Precio</TableCell>
                <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>URL</TableCell>
                <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>Estado</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Descripción</TableCell>
                <TableCell align="right" />
              </TableRow>
            </TableHead>
            <TableBody>
              {products.map((product) => (
                <TableRow key={product.id} hover>
                  <TableCell sx={{ maxWidth: { xs: 160, md: 360 } }}>
                    <Typography variant="body2" noWrap={false} sx={{ wordBreak: 'break-word' }}>
                      {product.name}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ display: { sm: 'none' } }}
                    >
                      {product.provider}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                    {product.provider}
                  </TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                    {product.category}
                  </TableCell>
                  <TableCell sx={{ minWidth: 160 }}>
                    <PriceBreakdown product={product} />
                    {countryFilter === 'all' && (
                      <Typography variant="caption" display="block" color="text.secondary">
                        {product.currency}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' }, maxWidth: 220 }}>
                    {product.safeToOpen ? (
                      <Link
                        href={verifyHref(product)}
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="body2"
                        sx={{ wordBreak: 'break-all' }}
                      >
                        {verifyHref(product)}
                      </Link>
                    ) : (
                      <Typography variant="caption" color="text.secondary" sx={{ wordBreak: 'break-all' }}>
                        {verifyHref(product)}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>
                    <Chip
                      size="small"
                      label={product.urlTrustLabel || '—'}
                      color={urlTrustColor(product.urlTrust)}
                    />
                  </TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                    <Chip
                      icon={getAvailabilityIcon(product.availability)}
                      label={product.availability}
                      color={getAvailabilityColor(product.availability)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, maxWidth: 260 }}>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      noWrap={false}
                      sx={{ wordBreak: 'break-word' }}
                    >
                      {product.stockText || '—'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    {product.safeToOpen ? (
                      <IconButton
                        component="a"
                        size="small"
                        href={verifyHref(product)}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label="Abrir ficha del producto"
                      >
                        <OpenInNew fontSize="small" />
                      </IconButton>
                    ) : (
                      <IconButton
                        size="small"
                        aria-label="Abrir ficha del producto"
                        disabled
                      >
                        <OpenInNew fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
