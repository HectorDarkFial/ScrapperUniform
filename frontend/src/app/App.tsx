import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { Products } from './components/Products';
import { Providers } from './components/Providers';
import { Export } from './components/Export';
import { Settings } from './components/Settings';
import { ScrapeJobProvider } from './context/ScrapeJobContext';
import { appTheme } from './theme';

export default function App() {
  return (
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <ScrapeJobProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/providers" element={<Providers />} />
            <Route path="/export" element={<Export />} />
            <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ScrapeJobProvider>
    </ThemeProvider>
  );
}
