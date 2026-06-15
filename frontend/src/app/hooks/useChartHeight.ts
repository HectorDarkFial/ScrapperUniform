import { useMediaQuery, useTheme } from '@mui/material';

export function useChartHeight() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  if (isMobile) return 220;
  if (isTablet) return 260;
  return 300;
}
