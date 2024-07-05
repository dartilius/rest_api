"use client";

import * as React from "react";
import { NextUIProvider } from "@nextui-org/system";
import { useRouter } from "next/navigation";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { ThemeProviderProps } from "next-themes/dist/types";
import { Provider as ReduxProvider } from "react-redux";

import ReduxToastrProvider from "../providers/ReduxToast";
import { store } from "../store/store";

export interface ProvidersProps {
  children: React.ReactNode;
  themeProps?: ThemeProviderProps;
}

export function Providers({ children, themeProps }: ProvidersProps) {
  const router = useRouter();

  return (
    <ReduxProvider store={store}>
      <NextUIProvider navigate={router.push}>
        <ReduxToastrProvider />
        <NextThemesProvider {...themeProps}>{children}</NextThemesProvider>
      </NextUIProvider>
    </ReduxProvider>
  );
}
