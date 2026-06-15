import { Paper, Typography, Box } from '@mui/material';
import { ResponsiveContainer } from 'recharts';
import type { ReactElement, ReactNode } from 'react';

interface ChartPanelProps {
  title: string;
  height: number;
  children: ReactNode;
  empty?: boolean;
  emptyMessage?: string;
}

export function ChartPanel({
  title,
  height,
  children,
  empty,
  emptyMessage = 'Sin datos todavía. Ejecutá un scraping desde Proveedores.',
}: ChartPanelProps) {
  return (
    <Paper sx={{ p: { xs: 1.5, sm: 2 }, height: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', sm: '1.15rem' } }}>
        {title}
      </Typography>
      {empty ? (
        <Box
          sx={{
            height,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'text.secondary',
            textAlign: 'center',
            px: 2,
          }}
        >
          <Typography variant="body2">{emptyMessage}</Typography>
        </Box>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          {children as ReactElement}
        </ResponsiveContainer>
      )}
    </Paper>
  );
}
