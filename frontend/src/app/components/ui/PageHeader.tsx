import type { ReactNode } from 'react';
import { Box, Typography, IconButton, Tooltip, CircularProgress, Chip } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  lastScrapeAt?: string | null;
  panelRefreshedAt?: Date | null;
  refreshIntervalSec?: number;
  isLiveUpdating?: boolean;
  onRefresh?: () => void;
  refreshing?: boolean;
  extra?: ReactNode;
}

export function PageHeader({
  title,
  subtitle,
  lastScrapeAt,
  panelRefreshedAt,
  refreshIntervalSec = 60,
  isLiveUpdating = false,
  onRefresh,
  refreshing,
  extra,
}: PageHeaderProps) {
  const scrapeLabel =
    lastScrapeAt &&
    new Date(lastScrapeAt).toLocaleString('es-AR', {
      dateStyle: 'short',
      timeStyle: 'short',
    });

  const panelLabel = panelRefreshedAt
    ? `Vista actualizada ${panelRefreshedAt.toLocaleTimeString('es-CL')}`
    : null;

  const intervalLabel = isLiveUpdating
    ? `En vivo · cada ${refreshIntervalSec}s`
    : `Auto-actualización cada ${refreshIntervalSec}s`;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        alignItems: { xs: 'flex-start', sm: 'center' },
        justifyContent: 'space-between',
        gap: 2,
        mb: 3,
      }}
    >
      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Typography variant="h4" component="h1" sx={{ fontSize: { xs: '1.5rem', sm: '2rem' } }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {subtitle}
          </Typography>
        )}
        <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {scrapeLabel && (
            <Chip size="small" label={`Último scrape: ${scrapeLabel}`} variant="outlined" />
          )}
          {panelLabel && (
            <Chip
              size="small"
              label={panelLabel}
              color={isLiveUpdating ? 'success' : 'default'}
              variant="outlined"
            />
          )}
          <Chip
            size="small"
            label={intervalLabel}
            color={isLiveUpdating ? 'info' : 'default'}
            variant="outlined"
          />
        </Box>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
        {extra}
        {onRefresh && (
          <Tooltip title="Actualizar datos">
            <span>
              <IconButton onClick={onRefresh} disabled={refreshing} aria-label="actualizar">
                {refreshing ? <CircularProgress size={22} /> : <RefreshIcon />}
              </IconButton>
            </span>
          </Tooltip>
        )}
      </Box>
    </Box>
  );
}
