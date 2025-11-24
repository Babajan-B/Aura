'use client';

import { useEffect, useState } from 'react';
import { getDigestHistory, getDigestById, submitFeedback, sendDigestEmail, DigestSummary, Digest, DigestItem } from '@/lib/api';
import Navigation from '@/components/Navigation';

export default function DigestsPage() {
  const [digestHistory, setDigestHistory] = useState<DigestSummary[]>([]);
  const [selectedDigest, setSelectedDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDigest, setLoadingDigest] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchDigestHistory();
  }, []);

  const fetchDigestHistory = async () => {
    try {
      const data = await getDigestHistory(20, 0);
      setDigestHistory(data.digests);
    } catch (error) {
      console.error('Error fetching digest history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDigest = async (digestId: string) => {
    setLoadingDigest(true);
    try {
      const digest = await getDigestById(digestId);
      setSelectedDigest(digest);
    } catch (error) {
      console.error('Error fetching digest:', error);
      alert('Failed to load digest. Please try again.');
    } finally {
      setLoadingDigest(false);
    }
  };

  const handleFeedback = async (digestItemId: string, contentId: string, feedbackValue: 'useful' | 'not_useful') => {
    try {
      await submitFeedback(digestItemId, contentId, feedbackValue);
      setFeedbackSubmitted(new Set([...feedbackSubmitted, digestItemId]));
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    }
  };

  const handleBackToList = () => {
    setSelectedDigest(null);
  };

  const handleSendEmail = async (digestId: string) => {
    try {
      await sendDigestEmail(digestId);
      alert('Email sent successfully!');
    } catch (error) {
      console.error('Error sending email:', error);
      alert('Failed to send email. Please try again.');
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
              Learning Digests
            </h1>
            <p className="text-lg text-gray-600">
              Your personalized learning content delivered weekly
            </p>
          </div>

          {!selectedDigest ? (
            // Digest History List
            <div className="bg-white rounded-lg p-8 border border-gray-200">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Digest History</h2>

              {loading ? (
                <div className="flex justify-center items-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : digestHistory.length === 0 ? (
                <div className="text-center py-12">
                  <div className="p-3 bg-gray-100 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                    <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">No Digests Yet</h3>
                  <p className="text-gray-600">Your learning digests will appear here once generated.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {digestHistory.map((digest) => (
                    <div
                      key={digest.digest_id}
                      onClick={() => handleSelectDigest(digest.digest_id)}
                      className="cursor-pointer rounded-lg border border-gray-200 bg-white p-6 hover:shadow-sm transition-shadow"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <div className="p-2 bg-pink-100 rounded-lg text-pink-600">
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            </div>
                            <div>
                              <h3 className="text-lg font-semibold text-gray-900">
                                {digest.goal_text.substring(0, 60)}
                                {digest.goal_text.length > 60 && '...'}
                              </h3>
                              <p className="text-sm text-gray-500">
                                {new Date(digest.week_start_date).toLocaleDateString()} - {new Date(digest.week_end_date).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <div className="px-4 py-2 bg-pink-600 text-white rounded-lg font-medium">
                              {digest.total_items} Items
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              {new Date(digest.generated_at).toLocaleDateString()}
                            </p>
                          </div>
                          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            // Selected Digest Detail View
            <div>
              {/* Back Button */}
              <button
                onClick={handleBackToList}
                className="mb-6 flex items-center space-x-2 text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                <span>Back to Digests</span>
              </button>

              {/* Digest Header */}
              <div className="bg-white rounded-lg p-8 mb-6 border border-gray-200">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                      {selectedDigest.goal_text}
                    </h2>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span className="flex items-center space-x-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <span>
                          {new Date(selectedDigest.week_start_date).toLocaleDateString()} - {new Date(selectedDigest.week_end_date).toLocaleDateString()}
                        </span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>Generated {new Date(selectedDigest.generated_at).toLocaleDateString()}</span>
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => handleSendEmail(selectedDigest.digest_id)}
                      className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      <span>Send Email</span>
                    </button>
                    <div className="px-5 py-3 bg-pink-600 text-white rounded-lg font-medium">
                      {selectedDigest.total_items} Items
                    </div>
                  </div>
                </div>
              </div>

              {/* Digest Items */}
              {loadingDigest ? (
                <div className="flex justify-center items-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="space-y-6">
                  {selectedDigest.items.map((item, index) => (
                    <div
                      key={item.digest_item_id}
                      className="rounded-lg border border-gray-200 bg-white shadow-sm"
                    >
                      <div className="p-6">
                        {/* Item Header */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <span className="flex items-center justify-center w-8 h-8 rounded-full bg-pink-600 text-white font-bold text-sm">
                                {index + 1}
                              </span>
                              <h3 className="text-xl font-semibold text-gray-900 flex-1">
                                {item.title}
                              </h3>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="px-3 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-medium uppercase">
                              {item.source_type}
                            </span>
                            <span className="px-3 py-1 rounded-full bg-gray-100 text-gray-800 text-xs font-medium">
                              Score: {item.relevance_score.toFixed(2)}
                            </span>
                          </div>
                        </div>

                        {/* Summary */}
                        <div className="mb-4">
                          <h4 className="text-sm font-medium text-gray-700 mb-2">Summary</h4>
                          <p className="text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-lg border border-gray-200">
                            {item.summary}
                          </p>
                        </div>

                        {/* Why It Matters */}
                        <div className="mb-4">
                          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center space-x-2">
                            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                            <span>Why It Matters</span>
                          </h4>
                          <p className="text-gray-700 leading-relaxed bg-blue-50 p-4 rounded-lg border border-blue-200">
                            {item.why_it_matters}
                          </p>
                        </div>

                        {/* Link and Feedback */}
                        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                          <a
                            href={item.link_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 font-medium transition-colors"
                          >
                            <span>Read More</span>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>

                          {/* Feedback Buttons */}
                          {feedbackSubmitted.has(item.digest_item_id) ? (
                            <span className="text-sm text-green-600 font-medium flex items-center space-x-1">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              <span>Feedback Submitted</span>
                            </span>
                          ) : (
                            <div className="flex items-center space-x-2">
                              <span className="text-sm text-gray-600 mr-2">Was this helpful?</span>
                              <button
                                onClick={() => handleFeedback(item.digest_item_id, item.digest_item_id, 'useful')}
                                className="p-2 rounded-lg bg-green-100 hover:bg-green-200 text-green-700 transition-colors"
                                title="Useful"
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                                </svg>
                              </button>
                              <button
                                onClick={() => handleFeedback(item.digest_item_id, item.digest_item_id, 'not_useful')}
                                className="p-2 rounded-lg bg-red-100 hover:bg-red-200 text-red-700 transition-colors"
                                title="Not Useful"
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
                                </svg>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
