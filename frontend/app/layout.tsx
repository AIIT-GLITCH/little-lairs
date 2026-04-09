import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/Nav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Little lAIrs — Citation Forensics Benchmark",
  description:
    "Which AI models fabricate sources? Reproducible, open benchmark testing URL citation accuracy across leading language models.",
  openGraph: {
    title: "Little lAIrs",
    description: "AI citation forensics benchmark. Who's lying?",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[#0d1117] text-gray-100 min-h-screen`}>
        <Nav />
        <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
        <footer className="border-t border-gray-800 mt-16 py-8 text-center text-gray-500 text-sm">
          <p>
            Little l<span className="text-red-400">AI</span>rs — Citation Forensics Benchmark
          </p>
          <p className="mt-1">
            <a href="https://github.com/AIIT-GLITCH/little-lairs" className="hover:text-gray-300">
              GitHub
            </a>
            {" · "}
            <a href="/methodology" className="hover:text-gray-300">Methodology</a>
            {" · "}
            <a href="/reproduce" className="hover:text-gray-300">Reproduce</a>
          </p>
        </footer>
      </body>
    </html>
  );
}
