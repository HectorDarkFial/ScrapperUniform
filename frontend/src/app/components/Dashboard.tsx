import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Alert, Skeleton, useMediaQuery, useTheme, Typography } from '@mui/material';
import Grid from '@mui/material/GridLegacy';
import { Inventory, Store, AttachMoney, Update } from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { api } from '../api/client';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { useChartHeight } from '../hooks/useChartHeight';
import { useScrapeJob } from '../context/ScrapeJobContext';
import { PageHeader } from './ui/PageHeader';
import { ChartPanel } from './ui/ChartPanel';
import { MetricCard } from './ui/MetricCard';
import { EmptyState } from './ui/EmptyState';
import { CurrencyBanner } from './ui/CurrencyBanner';
import {
  CountryTabs,
  countrySubtitle,
  formatMoney,
  formatMoneyByCode,
  DEFAULT_COUNTRY,
  CL_COLOR,
  AR_COLOR,
  type CountryFilter,
} from './ui/CountryTabs';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

type ChartClickState = {
  activePayload?: Array<{ payload?: { country?: string } }>;
};

export function Dashboard() {
  const navigate = useNavigate();
  const chartHeight = useChartHeight();
  const theme = useTheme();
  const compact = useMediaQuery(theme.breakpoints.down('sm'));
  const { job } = useScrapeJob();
  const [country, setCountry] = useState<CountryFilter>(DEFAULT_COUNTRY);

  const {
    data: metrics,
    error,
    loading,
    refreshing,
    reload,
    lastRefreshedAt,
    refreshIntervalSec,
    isScrapeActive,
  } = useAutoRefresh(() => api.metrics(country), [country]);

  const pickCountryFromChart = useCallback((state: ChartClickState) => {
    const code = state?.activePayload?.[0]?.payload?.country;
    if (code === 'CL' || code === 'AR') setCountry(code);
  }, []);

  if (loading && !metrics) {
    return (
      <Box>
        <Skeleton variant="text" width={240} height={40} sx={{ mb: 2 }} />
        <Grid container spacing={2}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Skeleton variant="rounded" height={110} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (error && !metrics) {
    return <Alert severity="error">No se pudieron cargar las métricas: {error}</Alert>;
  }

  if (!metrics) return null;

  const charts = metrics.charts;
  const hasProducts = metrics.totalProducts > 0;
  const avgLabel = formatMoney(metrics.avgPrice, country, metrics.currency);

  const compareSorted = [...(charts.countryCompare ?? [])].sort((a, b) =>
    a.country === 'CL' ? -1 : b.country === 'CL' ? 1 : 0
  );

  const providerBarColors = charts.providerData.map((p) =>
    p.country === 'CL' ? CL_COLOR : AR_COLOR
  );

  const historyCompare =
    country === 'all' && metrics.byCountry
      ? (() => {
          const dates = new Set<string>();
          metrics.byCountry.CL.charts.priceHistoryData.forEach((d) => dates.add(d.fecha));
          metrics.byCountry.AR.charts.priceHistoryData.forEach((d) => dates.add(d.fecha));
          return Array.from(dates)
            .sort()
            .map((fecha) => {
              const ar = metrics.byCountry!.AR.charts.priceHistoryData.find((d) => d.fecha === fecha);
              const cl = metrics.byCountry!.CL.charts.priceHistoryData.find((d) => d.fecha === fecha);
              return {
                fecha,
                chile: cl?.promedio ?? null,
                argentina: ar?.promedio ?? null,
              };
            });
        })()
      : charts.priceHistoryData;

  const compareXAxisTick = (tickProps: {
    x?: number;
    y?: number;
    payload?: { value?: string; index?: number };
  }) => {
    const { x = 0, y = 0, payload } = tickProps;
    const row =
      typeof payload?.index === 'number'
        ? compareSorted[payload.index]
        : compareSorted.find((item) => item.label === payload?.value);
    const code =
      (row as { currency?: string } | undefined)?.currency ??
      (row?.country === 'CL' ? 'CLP' : row?.country === 'AR' ? 'ARS' : '');
    const locale = row?.country === 'CL' ? 'es-CL' : 'es-AR';
    const avg =
      typeof row?.precioPromedio === 'number'
        ? row.precioPromedio.toLocaleString(locale, { maximumFractionDigits: 0 })
        : '—';

    return (
      <g transform={`translate(${x},${y})`}>
        <text textAnchor="middle" fill="currentColor" fontSize={11} fontWeight={600}>
          <tspan x={0} dy={12}>
            {payload?.value ?? row?.label ?? ''}
          </tspan>
          <tspan x={0} dy={16} fontSize={10} fontWeight={700} fill={row?.country === 'CL' ? CL_COLOR : AR_COLOR}>
            {code ? `prom. ${code} ${avg}` : avg}
          </tspan>
        </text>
      </g>
    );
  };

  const topPricesYAxisTick = (tickProps: {
    x?: number;
    y?: number;
    payload?: { value?: string; index?: number };
  }) => {
    const { x = 0, y = 0, payload } = tickProps;
    const row =
      typeof payload?.index === 'number'
        ? charts.priceData[payload.index]
        : charts.priceData.find((item) => item.name === payload?.value);
    const currency = row?.currency;
    const currencyColor =
      currency === 'CLP' ? CL_COLOR : currency === 'ARS' ? AR_COLOR : 'currentColor';

    return (
      <g transform={`translate(${x},${y})`}>
        <text textAnchor="end" fill="currentColor" fontSize={10}>
          <tspan x={0} dy={4}>
            {payload?.value ?? row?.name ?? ''}
          </tspan>
          {country === 'all' && currency ? (
            <tspan x={0} dy={14} fontSize={10} fontWeight={700} fill={currencyColor}>
              {currency}
            </tspan>
          ) : null}
        </text>
      </g>
    );
  };

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle={countrySubtitle(country)}
        lastScrapeAt={metrics.lastUpdate}
        panelRefreshedAt={lastRefreshedAt}
        refreshIntervalSec={refreshIntervalSec}
        isLiveUpdating={isScrapeActive}
        onRefresh={reload}
        refreshing={refreshing}
        extra={
          <>
            <CountryTabs value={country} onChange={setCountry} size="small" />
            {job?.running && (
              <Alert severity="info" sx={{ py: 0, px: 1.5, ml: 1 }}>
                Actualizando… {job.progress}%
              </Alert>
            )}
          </>
        }
      />

      <CurrencyBanner country={country} onSelectCountry={setCountry} />

      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
        Tip: hacé clic en una barra o segmento del gráfico para cambiar el país y ver precios en CLP o ARS.
      </Typography>

      {!hasProducts && (
        <Box sx={{ mb: 3 }}>
          <EmptyState
            title={
              country === 'all'
                ? 'Aún no hay productos'
                : `Sin productos de ${country === 'AR' ? 'Argentina' : 'Chile'}`
            }
            description="Los gráficos se actualizan al scrapear proveedores de ese país."
            actionLabel="Ir a Proveedores"
            onAction={() => navigate('/providers')}
          />
        </Box>
      )}

      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 2, sm: 3 } }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Productos"
            value={metrics.totalProducts}
            icon={<Inventory />}
            hint={country === 'all' ? 'Chile + Argentina' : undefined}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Proveedores Activos"
            value={metrics.activeProviders}
            icon={<Store />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard title="Precio Promedio" value={avgLabel} icon={<AttachMoney />} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Registros 24h"
            value={metrics.priceChanges24h}
            icon={<Update />}
          />
        </Grid>
      </Grid>

      {country === 'all' && compareSorted.length > 0 && (
        <Box sx={{ mb: { xs: 2, sm: 3 } }}>
          <ChartPanel
            title="Comparativa: Chile vs Argentina (clic para filtrar)"
            height={chartHeight}
            empty={false}
          >
            <BarChart
              data={compareSorted}
              onClick={pickCountryFromChart}
              style={{ cursor: 'pointer' }}
              margin={{ bottom: 28 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={compareXAxisTick} height={56} interval={0} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                formatter={(value: number, name: string) => [value, name]}
                labelFormatter={(_l, payload) => {
                  const row = payload?.[0]?.payload as {
                    country?: string;
                    precioPromedio?: number;
                  };
                  if (!row?.country) return '';
                  const moneda = row.country === 'CL' ? 'CLP' : 'ARS';
                  const locale = row.country === 'CL' ? 'es-CL' : 'es-AR';
                  return `${row.country === 'CL' ? 'Chile' : 'Argentina'} · ${moneda} · prom. ${
                    row.precioPromedio?.toLocaleString(locale, { maximumFractionDigits: 0 }) ?? '—'
                  }`;
                }}
              />
              <Legend />
              <Bar
                dataKey="productos"
                name="Productos"
                radius={[4, 4, 0, 0]}
                onClick={pickCountryFromChart}
              >
                {compareSorted.map((row, index) => (
                  <Cell
                    key={`cmp-${index}`}
                    fill={row.country === 'CL' ? CL_COLOR : AR_COLOR}
                  />
                ))}
              </Bar>
            </BarChart>
          </ChartPanel>
        </Box>
      )}

      <Grid container spacing={{ xs: 2, sm: 3 }}>
        <Grid item xs={12} lg={8}>
          <ChartPanel
            title={
              country === 'all'
                ? 'Precios promedio — Chile (CLP) y Argentina (ARS)'
                : `Evolución de precios en ${country === 'CL' ? 'CLP' : 'ARS'}`
            }
            height={chartHeight}
            empty={
              country === 'all'
                ? historyCompare.length === 0
                : charts.priceHistoryData.length === 0
            }
          >
            <LineChart
              data={historyCompare}
              onClick={(s) => {
                const key = s?.activePayload?.[0]?.dataKey;
                if (key === 'chile') setCountry('CL');
                if (key === 'argentina') setCountry('AR');
              }}
              style={{ cursor: country === 'all' ? 'pointer' : 'default' }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="fecha" tick={{ fontSize: compact ? 10 : 12 }} />
              <YAxis tick={{ fontSize: compact ? 10 : 12 }} width={compact ? 48 : 64} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  const moneda = name.includes('Chile') || name === 'chile' ? 'CLP' : 'ARS';
                  return [
                    value != null ? `${moneda} ${Number(value).toLocaleString('es-CL')}` : '—',
                    name,
                  ];
                }}
              />
              {!compact && <Legend />}
              {country === 'all' ? (
                <>
                  <Line
                    type="monotone"
                    dataKey="chile"
                    stroke={CL_COLOR}
                    strokeWidth={2}
                    name="Chile (CLP)"
                    dot={false}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="argentina"
                    stroke={AR_COLOR}
                    strokeWidth={2}
                    name="Argentina (ARS)"
                    dot={false}
                    connectNulls
                  />
                </>
              ) : (
                <Line
                  type="monotone"
                  dataKey="promedio"
                  stroke={country === 'CL' ? CL_COLOR : AR_COLOR}
                  strokeWidth={2}
                  name={`Promedio ${country === 'CL' ? 'CLP' : 'ARS'}`}
                  dot={false}
                />
              )}
            </LineChart>
          </ChartPanel>
        </Grid>

        <Grid item xs={12} lg={4}>
          <ChartPanel title="Productos por categoría" height={chartHeight} empty={charts.categoryData.length === 0}>
            <PieChart>
              <Pie
                data={charts.categoryData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={
                  compact
                    ? false
                    : (props: { name?: string; percent?: number }) =>
                        `${props.name ?? ''} ${((props.percent ?? 0) * 100).toFixed(0)}%`
                }
                outerRadius={compact ? 70 : 80}
                dataKey="value"
              >
                {charts.categoryData.map((entry: { name: string; value: number }, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ChartPanel>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartPanel
            title="Proveedores por país (clic en barra)"
            height={chartHeight}
            empty={charts.providerData.length === 0}
          >
            <BarChart
              data={charts.providerData}
              onClick={pickCountryFromChart}
              style={{ cursor: 'pointer' }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 9 }}
                interval={compact ? 'preserveStartEnd' : 0}
                angle={compact ? -30 : -15}
                textAnchor="end"
                height={compact ? 72 : 56}
              />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                formatter={(value: number) => [value, 'Productos']}
                labelFormatter={(_label, payload) => {
                  const row = payload?.[0]?.payload as { country?: string; name?: string };
                  const pais = row?.country === 'CL' ? 'Chile' : row?.country === 'AR' ? 'Argentina' : '';
                  const moneda = row?.country === 'CL' ? 'CLP' : row?.country === 'AR' ? 'ARS' : '';
                  return `${row?.name ?? ''} · ${pais} (${moneda})`;
                }}
              />
              <Bar dataKey="productos" name="Productos" radius={[4, 4, 0, 0]}>
                {charts.providerData.map((_, index) => (
                  <Cell key={`p-${index}`} fill={providerBarColors[index] ?? CL_COLOR} />
                ))}
              </Bar>
            </BarChart>
          </ChartPanel>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartPanel
            title={`Top precios · ${
              country === 'CL' ? 'CLP' : country === 'AR' ? 'ARS' : 'moneda local por producto'
            }`}
            height={chartHeight}
            empty={charts.priceData.length === 0}
          >
            <BarChart
              data={charts.priceData}
              layout="vertical"
              margin={{ left: country === 'all' ? 8 : 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis
                dataKey="name"
                type="category"
                width={country === 'all' ? (compact ? 118 : 156) : compact ? 90 : 140}
                tick={country === 'all' ? topPricesYAxisTick : { fontSize: 10 }}
              />
              <Tooltip
                formatter={(value: number, _n, item) => [
                  (() => {
                    const currency = item.payload.currency as string | undefined;
                    const countryCode =
                      currency === 'CLP' ? 'CL' : currency === 'ARS' ? 'AR' : undefined;
                    return formatMoneyByCode(Number(value), countryCode, currency);
                  })(),
                  'Precio',
                ]}
              />
              <Bar
                dataKey="precio"
                fill={country === 'CL' ? CL_COLOR : country === 'AR' ? AR_COLOR : CL_COLOR}
                name="Precio"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ChartPanel>
        </Grid>
      </Grid>
    </Box>
  );
}
