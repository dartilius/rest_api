// middleware.ts
import { NextResponse } from 'next/server';

export function middleware(request: Request) {
    const token = request.headers.get('Authorization');

    if (!token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    return NextResponse.next(); // Пропускаем дальше к API или странице
}

export const config = {
    matcher: ['/*'], // Применить к API и dashboard
};
