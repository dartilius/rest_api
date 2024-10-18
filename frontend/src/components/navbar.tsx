"use client"; // Ensure this file is treated as a client component

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import {
    Navbar as NextUINavbar,
    NavbarContent,
    NavbarMenu,
    NavbarMenuToggle,
    NavbarBrand,
    NavbarItem,
    NavbarMenuItem,
} from "@nextui-org/navbar";
import { Link } from "@nextui-org/link";
import { link as linkStyles } from "@nextui-org/theme";
import NextLink from "next/link";
import clsx from "clsx";

import { ThemeSwitch } from "./theme-switch";
import { siteConfig } from "@/src/config/site";
import { Button } from "@nextui-org/react";
import {GrVmMaintenance} from "react-icons/gr";

export const Navbar = () => {
    const [isMounted, setIsMounted] = useState(false);
    const pathname = usePathname(); // Use usePathname to get the current route path

    useEffect(() => {
        setIsMounted(true); // Ensuring the component has mounted before running any router logic
    }, []);

    if (!isMounted) {
        return null; // Do not render anything until the component is mounted on the client
    }

    return (
        <NextUINavbar className='max-w-6xl px-4' position="sticky">
            <NavbarContent className="basis-1/5 sm:basis-full" justify="start">
                <NavbarBrand className="gap-3 max-w-fit">
                    <NextLink className="flex justify-start items-center gap-1" href="/">
                        <GrVmMaintenance />
                        <p className="font-bold text-inherit">Админка RMC</p>
                    </NextLink>
                </NavbarBrand>
                <div className="hidden lg:flex gap-4 justify-start ml-2">
                    {siteConfig.navItems.map((item) => (
                        <NavbarItem key={item.href}>
                            <NextLink
                                className={clsx(
                                    linkStyles({ color: "foreground" }),
                                    pathname === item.href ? "text-primary font-medium" : ""
                                )}
                                href={item.href}
                            >
                                {item.label}
                            </NextLink>
                        </NavbarItem>
                    ))}
                </div>
            </NavbarContent>

            <NavbarContent className="hidden sm:flex basis-1/5 sm:basis-full" justify="end">
                <NavbarItem className="hidden sm:flex gap-2">
                    <ThemeSwitch />
                </NavbarItem>
                <NavbarItem className="hidden md:flex">
                    <Button
                        isExternal
                        as={Link}
                        className="text-sm font-normal text-default-600 bg-default-100"
                        variant="flat"
                    >
                        Sponsor
                    </Button>
                </NavbarItem>
            </NavbarContent>

            <NavbarContent className="sm:hidden basis-1 pl-4" justify="end">
                <ThemeSwitch />
                <NavbarMenuToggle />
            </NavbarContent>

            <NavbarMenu>
                <div className="mx-4 mt-2 flex flex-col gap-2">
                    {siteConfig.navMenuItems.map((item, index) => (
                        <NavbarMenuItem key={`${item}-${index}`}>
                            <Link
                                color={pathname === item.href ? "primary" : "foreground"}
                                href={item.href}
                                size="lg"
                            >
                                {item.label}
                            </Link>
                        </NavbarMenuItem>
                    ))}
                </div>
            </NavbarMenu>
        </NextUINavbar>
    );
};
