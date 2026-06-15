import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  List,
  ListItem,
  Alert,
  CircularProgress,
  Stack,
} from '@mui/material';
import Grid from '@mui/material/GridLegacy';
import { Add, Edit, Delete, PlayArrow, Refresh, CheckCircle, Stop } from '@mui/icons-material';
import { api } from '../api/client';
import { useScrapeJob } from '../context/ScrapeJobContext';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import { PageHeader } from './ui/PageHeader';
import { ScrapeProgressBanner } from './ui/ScrapeProgressBanner';
import { CountryTabs, countrySubtitle, DEFAULT_COUNTRY, type CountryFilter } from './ui/CountryTabs';
import type { Provider } from '../types';

function mapProvider(p: {
  id: string;
  name: string;
  country: 'AR' | 'CL';
  baseUrl: string;
  catalogUrls: string[];
  isActive: boolean;
  lastScrape?: string;
  productsCount: number;
}): Provider {
  return {
    id: p.id,
    slug: p.id,
    name: p.name,
    country: p.country,
    baseUrl: p.baseUrl,
    catalogUrls: p.catalogUrls,
    isActive: p.isActive,
    lastScrape: p.lastScrape,
    productsCount: p.productsCount,
  };
}

export function Providers() {
  const { watchJob, job, triggerRefresh } = useScrapeJob();
  const [countryFilter, setCountryFilter] = useState<CountryFilter>(DEFAULT_COUNTRY);
  const {
    data,
    error,
    loading,
    refreshing,
    reload,
  } = useAutoRefresh(async () => {
    const res = await api.sites(countryFilter === 'all' ? undefined : countryFilter);
    return res.providers.map(mapProvider);
  }, [countryFilter]);
  const providers = data ?? [];
  const [openDialog, setOpenDialog] = useState(false);
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null);
  const [actionError, setActionError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    country: 'AR' as 'AR' | 'CL',
    baseUrl: '',
    catalogUrls: [''],
    isActive: true,
  });
  const [scrapeMaxPages, setScrapeMaxPages] = useState(3);
  const [scrapeMaxProducts, setScrapeMaxProducts] = useState(50);

  const scraping = Boolean(job?.running);

  const handleOpenDialog = (provider?: Provider) => {
    if (provider) {
      setEditingProvider(provider);
      setFormData({
        name: provider.name,
        country: provider.country,
        baseUrl: provider.baseUrl,
        catalogUrls: provider.catalogUrls.length ? provider.catalogUrls : [''],
        isActive: provider.isActive,
      });
    } else {
      setEditingProvider(null);
      setFormData({
        name: '',
        country: 'AR',
        baseUrl: '',
        catalogUrls: [''],
        isActive: true,
      });
    }
    setOpenDialog(true);
  };

  const handleSave = async () => {
    setActionError('');
    const payload = {
      name: formData.name,
      country: formData.country,
      baseUrl: formData.baseUrl,
      catalogUrls: formData.catalogUrls.filter((u) => u.trim()),
      isActive: formData.isActive,
    };
    try {
      if (editingProvider) {
        await api.updateSite(editingProvider.id, payload);
      } else {
        await api.createSite(payload);
      }
      setOpenDialog(false);
      reload();
      triggerRefresh();
    } catch (e) {
      setActionError(String(e));
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('¿Eliminar este proveedor?')) return;
    try {
      await api.deleteSite(id);
      reload();
      triggerRefresh();
    } catch (e) {
      setActionError(String(e));
    }
  };

  const handleToggleActive = async (provider: Provider) => {
    try {
      await api.updateSite(provider.id, { isActive: !provider.isActive });
      reload();
      triggerRefresh();
    } catch (e) {
      setActionError(String(e));
    }
  };

  const handleScrape = async (siteSlug?: string) => {
    setActionError('');
    try {
      const res = await api.scrape({
        siteSlug: siteSlug || 'all',
        country: siteSlug ? undefined : countryFilter === 'all' ? 'all' : countryFilter,
        maxPages: scrapeMaxPages,
        maxProducts: scrapeMaxProducts,
        doExport: false,
      });
      watchJob(res.jobId);
    } catch (e) {
      setActionError(String(e));
    }
  };

  const handleStopScrape = async () => {
    if (!job?.jobId) return;
    setActionError('');
    try {
      await api.stopScrape(job.jobId);
    } catch (e) {
      setActionError(String(e));
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={6}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader
        title="Proveedores"
        subtitle={countrySubtitle(countryFilter)}
        onRefresh={reload}
        refreshing={refreshing}
        extra={
          <CountryTabs value={countryFilter} onChange={setCountryFilter} size="small" />
        }
      />

      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'flex-end',
          alignItems: { xs: 'stretch', sm: 'center' },
          gap: 1,
          mb: 2,
        }}
      >
        <Box sx={{ flex: 1 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ maxWidth: 420 }}>
            <TextField
              size="small"
              type="number"
              label="Máx. páginas"
              value={scrapeMaxPages}
              onChange={(e) => setScrapeMaxPages(Math.max(1, Number(e.target.value || 1)))}
              inputProps={{ min: 1 }}
              disabled={scraping}
            />
            <TextField
              size="small"
              type="number"
              label="Máx. productos"
              value={scrapeMaxProducts}
              onChange={(e) => setScrapeMaxProducts(Math.max(1, Number(e.target.value || 1)))}
              inputProps={{ min: 1 }}
              disabled={scraping}
            />
          </Stack>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            size="small"
            startIcon={scraping ? <CircularProgress size={18} /> : <Refresh />}
            onClick={() => handleScrape()}
            disabled={scraping}
          >
            {scraping ? 'Scrapeando…' : 'Iniciar Scraper'}
          </Button>
          <Button
            variant="outlined"
            color="error"
            size="small"
            startIcon={<Stop />}
            onClick={handleStopScrape}
            disabled={!scraping || !job?.jobId}
          >
            Detener scraping
          </Button>
          <Button variant="contained" startIcon={<Add />} onClick={() => handleOpenDialog()}>
            Agregar proveedor
          </Button>
        </Box>
      </Box>

      {(error || actionError) && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setActionError('')}>
          {actionError || error}
        </Alert>
      )}

      {scraping && job && <ScrapeProgressBanner job={job} />}

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                {countryFilter === 'all' ? 'Total proveedores' : 'En esta vista'}
              </Typography>
              <Typography variant="h3">{providers.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Activos
              </Typography>
              <Typography variant="h3" color="success.main">
                {providers.filter((p) => p.isActive).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        {countryFilter === 'all' && (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Argentina
                  </Typography>
                  <Typography variant="h3" color="primary.main">
                    {providers.filter((p) => p.country === 'AR').length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Chile
                  </Typography>
                  <Typography variant="h3" color="secondary.main">
                    {providers.filter((p) => p.country === 'CL').length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
        {countryFilter !== 'all' && (
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Productos scrapeados
                </Typography>
                <Typography variant="h3">
                  {providers.reduce((s, p) => s + p.productsCount, 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Estado</TableCell>
              <TableCell>Nombre</TableCell>
              <TableCell>País</TableCell>
              <TableCell>Productos</TableCell>
              <TableCell>Último Scrape</TableCell>
              <TableCell>URLs</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {providers.map((provider) => (
              <TableRow key={provider.id}>
                <TableCell>
                  <Switch
                    checked={provider.isActive}
                    onChange={() => handleToggleActive(provider)}
                    color="primary"
                  />
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center">
                    {provider.name}
                    {provider.isActive && (
                      <CheckCircle fontSize="small" color="success" sx={{ ml: 1 }} />
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={provider.country === 'AR' ? 'Argentina' : 'Chile'}
                    size="small"
                    color={provider.country === 'AR' ? 'primary' : 'secondary'}
                  />
                </TableCell>
                <TableCell>{provider.productsCount}</TableCell>
                <TableCell>
                  {provider.lastScrape
                    ? new Date(provider.lastScrape).toLocaleString('es-AR', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : 'Nunca'}
                </TableCell>
                <TableCell>
                  <Chip label={`${provider.catalogUrls.length} URL(s)`} size="small" />
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleScrape(provider.id)}
                    disabled={!provider.isActive || scraping}
                    color="primary"
                  >
                    <PlayArrow />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleOpenDialog(provider)} color="primary">
                    <Edit />
                  </IconButton>
                  <IconButton size="small" onClick={() => handleDelete(provider.id)} color="error">
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingProvider ? 'Editar Proveedor' : 'Agregar Proveedor'}</DialogTitle>
        <DialogContent>
          <Box mt={2}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  label="Nombre del Proveedor"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>País</InputLabel>
                  <Select
                    value={formData.country}
                    label="País"
                    onChange={(e) =>
                      setFormData({ ...formData, country: e.target.value as 'AR' | 'CL' })
                    }
                  >
                    <MenuItem value="AR">Argentina</MenuItem>
                    <MenuItem value="CL">Chile</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="URL Base"
                  value={formData.baseUrl}
                  onChange={(e) => setFormData({ ...formData, baseUrl: e.target.value })}
                  placeholder="https://ejemplo.com"
                />
              </Grid>
              <Grid item xs={12}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="subtitle2">URLs de Catálogo</Typography>
                  <Button
                    size="small"
                    startIcon={<Add />}
                    onClick={() =>
                      setFormData({ ...formData, catalogUrls: [...formData.catalogUrls, ''] })
                    }
                  >
                    Agregar URL
                  </Button>
                </Box>
                <List>
                  {formData.catalogUrls.map((url, index) => (
                    <ListItem
                      key={index}
                      secondaryAction={
                        formData.catalogUrls.length > 1 && (
                          <IconButton
                            edge="end"
                            onClick={() => {
                              const urls = [...formData.catalogUrls];
                              urls.splice(index, 1);
                              setFormData({ ...formData, catalogUrls: urls });
                            }}
                          >
                            <Delete />
                          </IconButton>
                        )
                      }
                    >
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="https://ejemplo.com/catalogo"
                        value={url}
                        onChange={(e) => {
                          const urls = [...formData.catalogUrls];
                          urls[index] = e.target.value;
                          setFormData({ ...formData, catalogUrls: urls });
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={
              !formData.name || !formData.baseUrl || !formData.catalogUrls.some((u) => u.trim())
            }
          >
            {editingProvider ? 'Guardar Cambios' : 'Agregar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
