import { Card, CardContent, Box, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  hint?: string;
}

export function MetricCard({ title, value, icon, hint }: MetricCardProps) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" gap={1}>
          <Box sx={{ minWidth: 0 }}>
            <Typography color="text.secondary" variant="body2" gutterBottom noWrap>
              {title}
            </Typography>
            <Typography
              variant="h4"
              sx={{ fontSize: { xs: '1.35rem', sm: '2rem' }, wordBreak: 'break-word' }}
            >
              {value}
            </Typography>
            {hint && (
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                {hint}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              bgcolor: 'primary.main',
              borderRadius: 2,
              p: { xs: 1, sm: 1.5 },
              color: 'white',
              flexShrink: 0,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
