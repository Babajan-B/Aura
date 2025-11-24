'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getActiveGoal, getSources, getCurrentDigest, Goal, Source, Digest } from '@/lib/api';
import Navigation from '@/components/Navigation';

export default function HomePage() {
  const [goal, setGoal] = useState<Goal | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [goalData, sourcesData, digestData] = await Promise.all([
          getActiveGoal(),
          getSources(),
          getCurrentDigest(),
        ]);
        setGoal(goalData);
        setSources(sourcesData);
        setDigest(digestData);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const activeSources = sources.filter((s) => s.status === 'active').length;

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Hero Section */}
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              Welcome to Your AI Learning Coach
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Personalized learning content delivered weekly, tailored to your goals and interests.
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {/* Active Goal Card */}
            <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                {loading && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                )}
              </div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Active Goal</h3>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : goal ? '1 Goal' : 'No Goal'}
              </p>
              {goal && (
                <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                  {goal.goal_text}
                </p>
              )}
            </div>

            {/* Total Sources Card */}
            <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                  </svg>
                </div>
                {loading && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
                )}
              </div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Total Sources</h3>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : `${activeSources} Active`}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                {sources.length} total sources
              </p>
            </div>

            {/* Latest Digest Card */}
            <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-pink-100 rounded-lg">
                  <svg className="w-6 h-6 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                {loading && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-pink-600"></div>
                )}
              </div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Latest Digest</h3>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : digest ? `${digest.total_items} Items` : 'No Digest'}
              </p>
              {digest && (
                <p className="text-sm text-gray-500 mt-2">
                  {new Date(digest.generated_at).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link
                href="/goals"
                className="rounded-lg p-6 bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                <div className="mb-3">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-1">Create Goal</h3>
                <p className="text-blue-100 text-sm">Set a new learning objective</p>
              </Link>

              <Link
                href="/sources"
                className="rounded-lg p-6 bg-purple-600 text-white hover:bg-purple-700 transition-colors"
              >
                <div className="mb-3">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-1">Add Source</h3>
                <p className="text-purple-100 text-sm">Connect new content sources</p>
              </Link>

              <Link
                href="/digests"
                className="rounded-lg p-6 bg-pink-600 text-white hover:bg-pink-700 transition-colors"
              >
                <div className="mb-3">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold mb-1">View Digests</h3>
                <p className="text-pink-100 text-sm">Browse your learning content</p>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
