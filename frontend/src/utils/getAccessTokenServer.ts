// utils/getAccessToken.ts
"use server"; // Делаем этот модуль серверным

import { cookies } from "next/headers";

export async function getServerAccessToken () {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("accessToken")?.value;
    return accessToken || null;
}
