import Link from "next/link";

const links = [
  { href: "/", label: "Leaderboard" },
  { href: "/methodology", label: "Methodology" },
  { href: "/reproduce", label: "Reproduce" },
  { href: "/prompts", label: "Prompts" },
  { href: "/changelog", label: "Changelog" },
  { href: "/limitations", label: "Limitations" },
];

export function Nav() {
  return (
    <nav className="border-b border-[#30363d] bg-[#161b22]">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
        <Link href="/" className="font-mono text-lg font-bold">
          Little l<span className="text-red-400">AI</span>rs
        </Link>
        <div className="flex items-center gap-4 ml-4">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm text-gray-400 hover:text-gray-100 transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </div>
        <div className="ml-auto">
          <a
            href="https://github.com/AIIT-GLITCH/little-lairs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-gray-500 hover:text-gray-300 font-mono"
          >
            GitHub →
          </a>
        </div>
      </div>
    </nav>
  );
}
