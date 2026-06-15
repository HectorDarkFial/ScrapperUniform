import {
  Box,
  Typography,
  Paper,
  Button,
  Divider,
  Card,
  CardContent,
  Alert,
} from '@mui/material';
import Grid from '@mui/material/GridLegacy';

export function Settings() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Configuración
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Panel y scraping
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Alert severity="info">
              Los parámetros HTTP, delays y exclusiones de dominios se editan en{' '}
              <code>config/settings.yaml</code>. Los proveedores se gestionan en la sección
              Proveedores y se sincronizan con <code>config/sites/*.yaml</code>.
            </Alert>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Línea de comandos
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Typography component="pre" sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, overflow: 'auto' }}>
              {`python manage.py import_sites
python manage.py scrape --country all
python -m src.cli.export_analysis`}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Información del Sistema
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Versión UI
                </Typography>
                <Typography variant="body1">1.0.0 (Material UI)</Typography>
              </Box>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Base de Datos
                </Typography>
                <Typography variant="body1">SQLite — data/uniforms.db</Typography>
              </Box>
              <Button variant="outlined" fullWidth href="/legacy/" sx={{ mb: 1 }}>
                Panel legacy (HTML)
              </Button>
              <Button variant="outlined" fullWidth href="/admin/">
                Administración Django
              </Button>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Documentación
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" paragraph>
                Consultá la carpeta <code>documentos/</code> en el repositorio (inicio, arquitectura, proveedores).
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
