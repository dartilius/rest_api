// middleware.ts

import { NextResponse, NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    const token = request.cookies.get('access_token')?.value;

    console.log('token', token);

    if (!token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    return NextResponse.next();
}


export const config = {
        matcher: ['/((?!_next).*)'], // Все страницы, кроме _next
};
