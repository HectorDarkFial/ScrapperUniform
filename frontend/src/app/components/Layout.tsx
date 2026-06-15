import { useState, type ReactNode } from 'react';
import {
  AppBar,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  IconButton,
  Container,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Inventory,
  Store,
  Menu as MenuIcon,
  Settings,
  Download,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useScrapeJob } from '../context/ScrapeJobContext';

const drawerWidth = 240;

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { job } = useScrapeJob();

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Productos', icon: <Inventory />, path: '/products' },
    { text: 'Proveedores', icon: <Store />, path: '/providers' },
    { text: 'Exportar', icon: <Download />, path: '/export' },
    { text: 'Configuración', icon: <Settings />, path: '/settings' },
  ];

  const legacyHref = '/legacy/';

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" fontWeight={700}>
          Scrapper Uniformes medicos
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
        <ListItem disablePadding sx={{ mt: 1 }}>
          <ListItemButton component="a" href={legacyHref}>
            <ListItemText
              primary="Panel legacy"
              secondary="Django HTML"
              primaryTypographyProps={{ fontSize: '0.9rem' }}
            />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          <IconButton
            color="inherit"
            aria-label="abrir menú"
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              flexGrow: 1,
              fontSize: { xs: '0.95rem', sm: '1.15rem' },
            }}
          >
            Monitoreo de Uniformes Clínicos
          </Typography>
          {job?.running && (
            <Chip
              size="small"
              color="info"
              label={
                job.progressMessage
                  ? `${job.progress}% · ${job.progressMessage.slice(0, 40)}`
                  : `Scraping ${job.progress}%`
              }
              sx={{ display: { xs: 'none', lg: 'flex' }, maxWidth: 320 }}
            />
          )}
        </Toolbar>
        {job?.running && (
          <LinearProgress
            variant="determinate"
            value={job.progress}
            sx={{ display: { xs: 'block', md: 'none' } }}
          />
        )}
      </AppBar>

      <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: 1,
              borderColor: 'divider',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          p: { xs: 1.5, sm: 2, md: 3 },
        }}
      >
        <Toolbar />
        <Container maxWidth="xl" disableGutters sx={{ px: { xs: 0, sm: 1 } }}>
          {children}
        </Container>
      </Box>
    </Box>
  );
}
