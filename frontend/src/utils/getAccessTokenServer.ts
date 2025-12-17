// utils/getAccessToken.ts
"use server";

import { cookies } from "next/headers";

export async function getServerAccessToken() {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("accessToken")?.value;
    return accessToken || null;
}
