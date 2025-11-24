'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getActiveGoal, createGoal, Goal } from '@/lib/api';
import Navigation from '@/components/Navigation';

export default function GoalsPage() {
  const router = useRouter();
  const [goal, setGoal] = useState<Goal | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    goalText: '',
    difficultyLevel: 'intermediate',
    frequency: 'weekly',
  });

  useEffect(() => {
    fetchGoal();
  }, []);

  const fetchGoal = async () => {
    try {
      const data = await getActiveGoal();
      setGoal(data);
    } catch (error) {
      console.error('Error fetching goal:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await createGoal(
        formData.goalText,
        formData.difficultyLevel,
        formData.frequency
      );
      await fetchGoal();
      setFormData({ goalText: '', difficultyLevel: 'intermediate', frequency: 'weekly' });
    } catch (error) {
      console.error('Error creating goal:', error);
      alert('Failed to create goal. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Navigation />
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-3">
              Learning Goals
            </h1>
            <p className="text-lg text-gray-600">
              Set your learning objectives and track your progress
            </p>
          </div>

          {/* Current Goal Display */}
          {loading ? (
            <div className="bg-white rounded-lg shadow-sm p-8 mb-8 border border-gray-200 flex justify-center items-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : goal ? (
            <div className="bg-white rounded-lg shadow-sm p-8 mb-8 border border-gray-200">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <h2 className="text-2xl font-semibold text-gray-900">Active Goal</h2>
                    <span className="px-3 py-1 rounded-full bg-green-100 text-green-800 text-sm font-medium">
                      Active
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    Created {new Date(goal.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="mb-6">
                <p className="text-lg text-gray-800 leading-relaxed">
                  {goal.goal_text}
                </p>
              </div>

              <div className="flex flex-wrap gap-4">
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {goal.difficulty_level}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="text-sm font-medium text-gray-700 capitalize">
                    {goal.frequency}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm p-8 mb-8 border border-gray-200 text-center">
              <div className="p-3 bg-gray-100 rounded-full w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">No Active Goal</h3>
              <p className="text-gray-600">Create your first learning goal below to get started.</p>
            </div>
          )}

          {/* Create New Goal Form */}
          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <div className="mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">
                {goal ? 'Update Your Goal' : 'Create New Goal'}
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Goal Text */}
              <div>
                <label htmlFor="goalText" className="block text-sm font-medium text-gray-700 mb-2">
                  What do you want to learn?
                </label>
                <textarea
                  id="goalText"
                  rows={4}
                  required
                  value={formData.goalText}
                  onChange={(e) => setFormData({ ...formData, goalText: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 resize-none"
                  placeholder="e.g., I want to learn about machine learning and AI to build intelligent applications..."
                />
              </div>

              {/* Difficulty Level */}
              <div>
                <label htmlFor="difficultyLevel" className="block text-sm font-medium text-gray-700 mb-2">
                  Difficulty Level
                </label>
                <select
                  id="difficultyLevel"
                  value={formData.difficultyLevel}
                  onChange={(e) => setFormData({ ...formData, difficultyLevel: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                >
                  <option value="beginner">Beginner - I'm just starting out</option>
                  <option value="intermediate">Intermediate - I have some knowledge</option>
                  <option value="advanced">Advanced - I'm experienced</option>
                </select>
              </div>

              {/* Frequency */}
              <div>
                <label htmlFor="frequency" className="block text-sm font-medium text-gray-700 mb-2">
                  Learning Frequency
                </label>
                <select
                  id="frequency"
                  value={formData.frequency}
                  onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                >
                  <option value="now">Now - Generate digest immediately</option>
                  <option value="daily">Daily - Receive content every day</option>
                  <option value="weekly">Weekly - Receive content once a week</option>
                  <option value="biweekly">Biweekly - Receive content every two weeks</option>
                </select>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitting || !formData.goalText.trim()}
                className="w-full py-3 px-6 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? (
                  <span className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>{formData.frequency === 'now' ? 'Creating Goal & Generating Digest...' : 'Creating Goal...'}</span>
                  </span>
                ) : (
                  <span>{goal ? 'Update Goal' : 'Create Goal'}</span>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
