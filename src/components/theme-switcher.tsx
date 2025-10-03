import * as React from "react";
import { useThemeConfig } from "@/contexts/theme-context";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ThemeSwitcherProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function ThemeSwitcher({ className, ...props }: ThemeSwitcherProps) {
  const { themes, theme: currentTheme, setTheme } = useThemeConfig();
  const currentThemeData = themes.find((t) => t.value === currentTheme) || themes[0];
  const ThemeIcon = currentThemeData?.icon;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9"
          aria-label="Select a theme"
        >
          <ThemeIcon className="h-5 w-5" />
          <span className="sr-only">Theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[200px]">
        {themes.map((theme) => {
          const Icon = theme.icon;
          return (
            <DropdownMenuItem
              key={theme.value}
              className="flex items-center gap-2"
              onClick={() => setTheme(theme.value)}
            >
              <Icon className="h-4 w-4" />
              <span>{theme.label}</span>
              {theme.value === currentTheme && (
                <span className="ml-auto text-primary">
                  ✓
                </span>
              )}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
