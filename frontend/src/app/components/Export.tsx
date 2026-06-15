import { useEffect, useRef, useState } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Card,
  CardContent,
  Divider,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  CircularProgress,
  LinearProgress,
} from '@mui/material';
import Grid from '@mui/material/GridLegacy';
import { Download, TableChart, Description, CheckCircle, Info } from '@mui/icons-material';
import { api, downloadExportFile } from '../api/client';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { useScrapeJob } from '../context/ScrapeJobContext';
import { PageHeader } from './ui/PageHeader';

function pickPrimaryExportName(
  exportFiles?: { name: string; key: string }[],
  paths?: Record<string, string>
): string | null {
  if (exportFiles?.length) {
    const informe = exportFiles.find((f) => f.key === 'informe');
    return informe?.name ?? exportFiles[0].name;
  }
  if (paths) {
    const raw = paths.informe ?? paths.productos ?? Object.values(paths)[0];
    if (raw) {
      const parts = raw.split(/[/\\]/);
      return parts[parts.length - 1] || null;
    }
  }
  return null;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function Export() {
  const [format, setFormat] = useState<'csv' | 'xlsx'>('xlsx');
  const [exportSuccess, setExportSuccess] = useState(false);
  const [lastDownloadName, setLastDownloadName] = useState<string | null>(null);
  const [error, setError] = useState('');
  const { watchJob, job } = useScrapeJob();
  const exportJobId = useRef<number | null>(null);
  const wasExportRunning = useRef(false);

  const {
    data: exportsData,
    refreshing,
    reload: reloadFiles,
  } = useAutoRefresh(() => api.exportsList(), []);

  const { data: readiness, reload: reloadReadiness } = useAutoRefresh(
    () => api.exportReadiness(),
    []
  );

  const recentExports = exportsData?.exports ?? [];
  const exportRunning = Boolean(job?.running && job?.jobType === 'export');
  const canExport = Boolean(readiness?.canExport) && !exportRunning;
  const showBlockingWarning =
    readiness && !readiness.canExport && !exportRunning && readiness.message;

  useEffect(() => {
    const isOurExportJob =
      job?.jobType === 'export' && exportJobId.current != null && job.jobId === exportJobId.current;

    if (wasExportRunning.current && isOurExportJob && job && !job.running) {
      if (job.status === 'done') {
        const fileName = pickPrimaryExportName(job.exportFiles, job.result?.export_paths);
        if (fileName) {
          downloadExportFile(fileName);
          setLastDownloadName(fileName);
        }
        setExportSuccess(true);
        reloadFiles();
        reloadReadiness();
        const t = setTimeout(() => setExportSuccess(false), 6000);
        wasExportRunning.current = false;
        return () => clearTimeout(t);
      }
      if (job.status === 'error') {
        setError(job.error || 'No se pudo generar el archivo.');
      }
      wasExportRunning.current = false;
    }

    if (isOurExportJob && job?.running) {
      wasExportRunning.current = true;
    }
  }, [job, reloadFiles, reloadReadiness]);

  const handleExport = async () => {
    setError('');
    setExportSuccess(false);
    setLastDownloadName(null);
    try {
      const res = await api.export({ format: format === 'csv' ? 'csv' : 'xlsx' });
      exportJobId.current = res.jobId;
      wasExportRunning.current = true;
      watchJob(res.jobId);
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <Box>
      <PageHeader
        title="Exportar datos"
        subtitle="Primero completá el scraping en Proveedores. Cuando haya productos con precio, generá y descargá el informe."
        onRefresh={() => {
          reloadFiles();
          reloadReadiness();
        }}
        refreshing={refreshing}
      />

      {showBlockingWarning && (
        <Alert severity="warning" icon={<Info />} sx={{ mb: 3 }}>
          {readiness!.message}
          {readiness.exportableProducts > 0 && readiness.totalProducts > 0 && (
            <>
              {' '}
              ({readiness.exportableProducts} de {readiness.totalProducts} productos listos)
            </>
          )}
        </Alert>
      )}

      {readiness?.canExport && !exportRunning && (
        <Alert severity="success" variant="outlined" sx={{ mb: 3 }}>
          {readiness.exportableProducts} productos listos para exportar.
          {readiness.lastScrapeAt && (
            <> Último scraping: {new Date(readiness.lastScrapeAt).toLocaleString('es-AR')}.</>
          )}
          {readiness.securityNote && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              {readiness.securityNote}
            </Typography>
          )}
        </Alert>
      )}

      {exportSuccess && (
        <Alert severity="success" icon={<CheckCircle />} sx={{ mb: 3 }}>
          {lastDownloadName ? (
            <>
              Descarga iniciada: <strong>{lastDownloadName}</strong>. Si no apareció, usá el botón
              de descarga en la lista de la derecha.
            </>
          ) : (
            'Exportación completada. Descargá el archivo desde la lista de exportaciones.'
          )}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      {exportRunning && (
        <Box mb={3}>
          <Alert severity="info" sx={{ mb: 1 }}>
            Generando archivos… {job?.progress ?? 0}%
            {job?.progressMessage ? ` — ${job.progressMessage}` : ''}
          </Alert>
          <LinearProgress variant="determinate" value={job?.progress ?? 0} />
        </Box>
      )}

      <Grid container spacing={{ xs: 2, sm: 3 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Formato</InputLabel>
                    <Select
                      value={format}
                      label="Formato"
                      onChange={(e) => setFormat(e.target.value as 'csv' | 'xlsx')}
                      disabled={exportRunning}
                    >
                      <MenuItem value="xlsx">
                        <Box display="flex" alignItems="center" gap={1}>
                          <TableChart fontSize="small" /> Excel (.xlsx)
                        </Box>
                      </MenuItem>
                      <MenuItem value="csv">
                        <Box display="flex" alignItems="center" gap={1}>
                          <Description fontSize="small" /> CSV
                        </Box>
                      </MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    size="large"
                    fullWidth
                    startIcon={
                      exportRunning ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <Download />
                      )
                    }
                    onClick={handleExport}
                    disabled={!canExport || exportRunning}
                  >
                    {canExport
                      ? 'Generar y descargar informe'
                      : 'Exportar (requiere scraping completado)'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Exportaciones recientes
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {recentExports.length === 0 ? (
                <Alert severity="info" variant="outlined">
                  Todavía no hay archivos. Generá un informe con el botón de arriba.
                </Alert>
              ) : (
                <List dense>
                  {recentExports.map((f) => (
                    <ListItem key={f.name} disablePadding sx={{ mb: 1 }}>
                      <ListItemText
                        primary={f.name}
                        secondary={`${formatFileSize(f.size)} · ${new Date(f.modified * 1000).toLocaleString('es-AR')}`}
                        primaryTypographyProps={{ noWrap: true, title: f.name }}
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          aria-label={`Descargar ${f.name}`}
                          onClick={() => downloadExportFile(f.name)}
                          size="small"
                        >
                          <Download fontSize="small" />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
