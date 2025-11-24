import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const loggedIn = req.cookies.get("logged_in")?.value === "1";

  // Protect these paths
  const protectedPaths = ["/chatbase/:path*", "/components/chatpage", "/chatbase"];
  const isProtected = protectedPaths.some((p) => req.nextUrl.pathname.startsWith(p));

  if (isProtected && !loggedIn) {
    const url = new URL("/login", req.url);
    url.searchParams.set("next", req.nextUrl.pathname);
    return NextResponse.redirect(url);
  }

  // Optional: prevent visiting /login if already logged in
  if (req.nextUrl.pathname === "/login" && loggedIn) {
    return NextResponse.redirect(new URL("/chatbase", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/components/chatpage", "/chatbase/:path*", "/chatbase"],
};
