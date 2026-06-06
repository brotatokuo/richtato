function cssVarHsl(name: string, fallback: string): string {
  if (typeof window === 'undefined') {
    return fallback;
  }

  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();

  if (!value) {
    return fallback;
  }

  return `hsl(${value})`;
}

export function getJoyrideThemeOptions() {
  return {
    arrowColor: cssVarHsl('--popover', '#ffffff'),
    backgroundColor: cssVarHsl('--popover', '#ffffff'),
    primaryColor: cssVarHsl('--primary', '#0f172a'),
    textColor: cssVarHsl('--popover-foreground', '#0f172a'),
    overlayColor: 'rgba(0, 0, 0, 0.55)',
    zIndex: 10000,
  };
}
