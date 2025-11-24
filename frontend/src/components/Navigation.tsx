'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FC } from 'react';

const Navigation: FC = () => {
  const pathname = usePathname();

  const navLinks = [
    { href: '/', label: 'Dashboard' },
    { href: '/goals', label: 'Goals' },
    { href: '/sources', label: 'Sources' },
    { href: '/digests', label: 'Digests' },
  ];

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === href;
    }
    return pathname.startsWith(href);
  };

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-lg bg-white/70 border-b border-gray-200/50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2 group">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-lg blur opacity-50 group-hover:opacity-75 transition-opacity"></div>
              <div className="relative bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white px-3 py-2 rounded-lg font-bold text-xl">
                AI
              </div>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Learning Coach
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`relative px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  isActive(link.href)
                    ? 'text-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/50'
                }`}
              >
                {isActive(link.href) && (
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-lg shadow-lg shadow-indigo-500/30"></div>
                )}
                <span className="relative z-10">{link.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
