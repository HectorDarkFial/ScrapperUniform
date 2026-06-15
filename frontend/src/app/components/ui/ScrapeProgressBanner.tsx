import { Alert, Box, LinearProgress, Typography } from '@mui/material';
import type { JobStatusResponse } from '../../api/client';
import { formatEta } from '../../utils/formatEta';

interface ScrapeProgressBannerProps {
  job: JobStatusResponse;
  compact?: boolean;
}

export function ScrapeProgressBanner({ job, compact = false }: ScrapeProgressBannerProps) {
  const meta = job.progressMeta;
  const eta = formatEta(job.etaSeconds);
  const siteLine =
    meta?.totalSites && meta.totalSites > 1 && meta.siteIndex
      ? `Proveedor ${meta.siteIndex}/${meta.totalSites}`
      : null;
  const productLine =
    meta?.productsTotal && meta.phase === 'products'
      ? ` · producto ${meta.productsDone ?? 0}/${meta.productsTotal}`
      : '';

  const message =
    job.progressMessage ||
    (meta?.currentSite ? `${meta.currentSite}${productLine}` : 'Scraping en curso…');

  if (compact) {
    return (
      <Box sx={{ width: '100%' }}>
        <Typography variant="caption" display="block" noWrap>
          {message}
          {eta ? ` · ${eta}` : ''}
        </Typography>
        <LinearProgress variant="determinate" value={job.progress ?? 0} sx={{ mt: 0.5 }} />
      </Box>
    );
  }

  return (
    <Box mb={3}>
      <Alert severity="info" sx={{ mb: 1 }}>
        <Typography variant="body2" fontWeight={600}>
          {message}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          {siteLine}
          {siteLine && eta ? ' · ' : ''}
          {eta ? `Tiempo estimado restante: ${eta}` : 'Calculando tiempo estimado…'}
          {' · '}
          {job.progress ?? 0}% completado
          {typeof job.productsForJob === 'number'
            ? ` · ${job.productsForJob} productos en esta corrida`
            : typeof job.productsInDb === 'number'
              ? ` · ${job.productsInDb} en base`
              : ''}
        </Typography>
      </Alert>
      <LinearProgress variant="determinate" value={job.progress ?? 0} />
    </Box>
  );
}
