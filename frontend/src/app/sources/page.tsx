'use client';

import { useEffect, useState } from 'react';
import { getSources, addSource, seedDefaultSources, Source } from '@/lib/api';
import Navigation from '@/components/Navigation';

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [adding, setAdding] = useState(false);
  const [formData, setFormData] = useState({
    sourceType: 'rss',
    value: '',
  });

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const data = await getSources();
      setSources(data);
    } catch (error) {
      console.error('Error fetching sources:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedDefaults = async () => {
    setSeeding(true);
    try {
      const result = await seedDefaultSources();
      alert(`Successfully added ${result.sources_added} default sources!`);
      await fetchSources();
    } catch (error) {
      console.error('Error seeding sources:', error);
      alert('Failed to seed default sources. Please try again.');
    } finally {
      setSeeding(false);
    }
  };

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);

    try {
      await addSource(formData.sourceType, formData.value);
      setFormData({ sourceType: 'rss', value: '' });
      await fetchSources();
    } catch (error) {
      console.error('Error adding source:', error);
      alert('Failed to add source. Please try again.');
    } finally {
      setAdding(false);
    }
  };

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'rss':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 5c7.18 0 13 5.82 13 13M6 11a7 7 0 017 7m-6 0a1 1 0 11-2 0 1 1 0 012 0z" />
          </svg>
        );
      case 'youtube':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
          </svg>
        );
      case 'reddit':
        return (
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
        );
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === 'active') {
      return (
        <span className="px-3 py-1 rounded-full bg-gradient-to-r from-green-400 to-emerald-500 text-white text-xs font-semibold shadow">
          Active
        </span>
      );
    } else if (status === 'disabled') {
      return (
        <span className="px-3 py-1 rounded-full bg-gray-400 text-white text-xs font-semibold shadow">
          Disabled
        </span>
      );
    } else {
      return (
        <span className="px-3 py-1 rounded-full bg-red-400 text-white text-xs font-semibold shadow">
          Error
        </span>
      );
    }
  };

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-3">
              Content Sources
            </h1>
            <p className="text-lg text-gray-600">
              Manage your learning content sources
            </p>
          </div>

          {/* Seed Default Sources Button */}
          {sources.length === 0 && !loading && (
            <div className="bg-white rounded-lg p-8 mb-8 border border-gray-200 text-center">
              <div className="p-3 bg-blue-100 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-1">No Sources Yet</h3>
              <p className="text-gray-600 mb-4">Get started quickly by adding default RSS feeds</p>
              <button
                onClick={handleSeedDefaults}
                disabled={seeding}
                className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center space-x-2"
              >
                {seeding ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Adding Sources...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>Add Default Sources</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Add Custom Source Form */}
          <div className="bg-white rounded-lg p-8 mb-8 border border-gray-200">
            <div className="mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">Add Custom Source</h2>
            </div>

            <form onSubmit={handleAddSource} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Source Type */}
                <div>
                  <label htmlFor="sourceType" className="block text-sm font-medium text-gray-700 mb-2">
                    Source Type
                  </label>
                  <select
                    id="sourceType"
                    value={formData.sourceType}
                    onChange={(e) => setFormData({ ...formData, sourceType: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  >
                    <option value="rss">RSS Feed</option>
                    <option value="youtube">YouTube Channel</option>
                    <option value="reddit">Reddit</option>
                    <option value="x_api">X/Twitter</option>
                    <option value="website">Website</option>
                  </select>
                </div>

                {/* Source Value */}
                <div className="md:col-span-2">
                  <label htmlFor="value" className="block text-sm font-medium text-gray-700 mb-2">
                    Source URL or Identifier
                  </label>
                  <input
                    type="text"
                    id="value"
                    required
                    value={formData.value}
                    onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                    placeholder="e.g., https://example.com/feed.rss"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={adding || !formData.value.trim()}
                className="w-full py-3 px-6 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {adding ? 'Adding Source...' : 'Add Source'}
              </button>
            </form>
          </div>

          {/* Sources List */}
          <div className="bg-white rounded-lg p-8 border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">Your Sources</h2>
              {sources.length > 0 && !loading && (
                <button
                  onClick={handleSeedDefaults}
                  disabled={seeding}
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  {seeding ? 'Adding...' : 'Add Defaults'}
                </button>
              )}
            </div>

            {loading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : sources.length === 0 ? (
              <div className="text-center py-12">
                <div className="p-3 bg-gray-100 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                </div>
                <p className="text-gray-600">No sources added yet</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sources.map((source) => (
                  <div
                    key={source.source_id}
                    className="rounded-lg border border-gray-200 bg-white p-5 hover:shadow-sm transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-gray-100 rounded-lg text-gray-600">
                          {getSourceIcon(source.source_type)}
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                            {source.source_type}
                          </p>
                        </div>
                      </div>
                      {getStatusBadge(source.status)}
                    </div>

                    <p className="text-sm text-gray-700 break-all mb-3 font-mono bg-gray-50 p-2 rounded border border-gray-200">
                      {source.value}
                    </p>

                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>
                        Added {new Date(source.created_at).toLocaleDateString()}
                      </span>
                      {source.last_fetched_at && (
                        <span>
                          Fetched {new Date(source.last_fetched_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
