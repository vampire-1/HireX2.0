"use client";

import Link from "next/link";
import SiteLogo from "@/assets/logo.svg";
import { CodeXml, Feather, MenuIcon, Newspaper, Wallet2 } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useState } from "react";
import { ActionButton } from "@/components/action-button";
import { useRouter } from "next/navigation";

export default function SiteHeader() {
    const [isOpen, setIsOpen] = useState(false);
    const [isChatbaseLoaded, setIsChatbaseLoaded] = useState(false);

    const handleAskLexoraClick = () => {
        if (!isChatbaseLoaded) {
            // Dynamically load the Chatbase script
            const script = document.createElement("script");
            script.src = "https://www.chatbase.co/embed.min.js";
            script.setAttribute("chatbotId", "7-wY8Jr7Bpqe0DJjAb3nx");
            script.setAttribute("domain", "www.chatbase.co");
            script.defer = true;
            script.onload = () => {
                // Set loaded flag after script has loaded
                setIsChatbaseLoaded(true);
                // Initialize and open the chatbot
                if (window.Chatbase && typeof window.Chatbase.openChat === 'function') {
                    window.Chatbase.openChat();
                } else {
                    console.error("Chatbase object or openChat method not found.");
                }
            };
            document.body.appendChild(script);
        } else {
            // If script is already loaded, just open the chat
            if (window.Chatbase && typeof window.Chatbase.openChat === 'function') {
                window.Chatbase.openChat();
            } else {
                console.error("Chatbase object or openChat method not found.");
            }
        }
    };

    const router = useRouter()

    return (
        <>
            <header className={"py-4 border-b max-md:backdrop-blur md:border-none sticky top-0 z-10"}>
                <div className={"container max-md:px-4"}>
                    <div className={"flex items-center justify-between md:border md:p-2.5 md:rounded-xl max-w-2xl mx-auto md:backdrop-blur "}>
                        <Link href={"/"}>
                            <div className={"border size-10 rounded-lg inline-flex items-center justify-center"}>
                                <SiteLogo className={"size-8 h-auto"} />
                            </div>
                        </Link>
                        <section className={"max-md:hidden"}>
                            <nav className={"flex gap-8 items-center text-sm"}>
                                <Link href={"#"} className={"text-white/70 hover:text-white transition"}>Home</Link>
                                <Link href={"#features"} className={"text-white/70 hover:text-white transition"}>Features</Link>
                                <Link href={"#about"} className={"text-white/70 hover:text-white transition"}>About</Link>
                                <Link href={"#content"} className={"text-white/70 hover:text-white transition"}>Connect</Link>
                            </nav>
                        </section>
                        <section className={"flex max-md:gap-4 items-center"}>
                            <ActionButton label={"Ask HireX"} onClick={() => router.push("/auth")} />
                            <Sheet open={isOpen} onOpenChange={setIsOpen}>
                                <SheetTrigger>
                                    <MenuIcon className={"size-9 md:hidden hover:text-white/70 transition"} />
                                </SheetTrigger>
                                <SheetContent side={"top"} className={"p-8"}>
                                    <div className={"inline-flex items-center center gap-3"}>
                                        <div className={"border size-8 rounded-lg inline-flex items-center justify-center"}>
                                            <SiteLogo className={"size-6 h-auto"} />
                                        </div>
                                        <p className={"font-bold"}>HireX</p>
                                    </div>
                                    <div className={"mt-8 mb-4"}>
                                        <nav className={"grid gap-4 items-center text-lg"}>
                                            <Link href={"#"} className={"flex items-center gap-3 text-white/70 hover:text-white transition"}>
                                                <Feather className={"size-6"} />
                                                Home
                                            </Link>
                                            <Link href={"#features"} className={"flex items-center gap-3 text-white/70 hover:text-white transition"}>
                                                <CodeXml className={"size-6"} />
                                                Features
                                            </Link>
                                            <Link href={"#about"} className={"flex items-center gap-3 text-white/70 hover:text-white transition"}>
                                                <Wallet2 className={"size-6"} />
                                                About
                                            </Link>
                                            <Link href={"#content"} className={"flex items-center gap-3 text-white/70 hover:text-white transition"}>
                                                <Newspaper className={"size-6"} />
                                                Connect
                                            </Link>
                                        </nav>
                                    </div>
                                </SheetContent>
                            </Sheet>
                        </section>
                    </div>
                </div>
            </header>
        </>
    );
}
