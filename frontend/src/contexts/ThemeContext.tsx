import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type Theme = 'light' | 'dark' | 'discord';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>('light');

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const initialTheme = savedTheme || systemTheme;
    
    setThemeState(initialTheme);
    updateDocumentTheme(initialTheme);
  }, []);

  const updateDocumentTheme = (newTheme: Theme) => {
    // Remove all theme classes
    document.documentElement.classList.remove('dark', 'discord');
    
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else if (newTheme === 'discord') {
      document.documentElement.classList.add('discord', 'dark');
      // Add Discord-specific styling
      document.documentElement.style.setProperty('--discord-bg', '#36393f');
      document.documentElement.style.setProperty('--discord-secondary', '#2f3136');
      document.documentElement.style.setProperty('--discord-tertiary', '#202225');
      document.documentElement.style.setProperty('--discord-accent', '#7289da');
      document.documentElement.style.setProperty('--discord-pink', '#ff73fa');
      document.documentElement.style.setProperty('--discord-green', '#43b581');
    } else {
      // Light theme
      document.documentElement.style.removeProperty('--discord-bg');
      document.documentElement.style.removeProperty('--discord-secondary');
      document.documentElement.style.removeProperty('--discord-tertiary');
      document.documentElement.style.removeProperty('--discord-accent');
      document.documentElement.style.removeProperty('--discord-pink');
      document.documentElement.style.removeProperty('--discord-green');
    }
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
    updateDocumentTheme(newTheme);
  };

  const toggleTheme = () => {
    const themeOrder: Theme[] = ['light', 'dark', 'discord'];
    const currentIndex = themeOrder.indexOf(theme);
    const newTheme = themeOrder[(currentIndex + 1) % themeOrder.length];
    setTheme(newTheme);
  };

  const value: ThemeContextType = {
    theme,
    toggleTheme,
    setTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};