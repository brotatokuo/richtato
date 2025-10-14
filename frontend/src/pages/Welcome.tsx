import { ArrowRight, Shield, TrendingUp, Zap } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Welcome() {
  const { demoLogin } = useAuth();
  const navigate = useNavigate();
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const handleDemoLogin = async () => {
    try {
      setIsLoggingIn(true);
      setLoginError(null);
      await demoLogin();
      // Navigate to dashboard after successful login
      navigate('/budget');
    } catch (error) {
      console.error('Demo login failed:', error);
      setLoginError(
        error instanceof Error ? error.message : 'Demo login failed'
      );
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-primary/10 dark:from-slate-950 dark:via-black dark:to-slate-900 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-grid-slate-100 dark:bg-grid-slate-800/25 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0.5))]"></div>
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-r from-primary/20 to-secondary/20 dark:from-primary/10 dark:to-secondary/20 rounded-full blur-3xl"></div>

      <div className="relative z-10 flex items-center justify-center min-h-screen p-4">
        <div className="w-full max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            {/* Logo Section */}
            <div className="mb-8">
              <div className="relative inline-block">
                <img
                  src="/richtato.png"
                  alt="Richtato Logo"
                  className="w-40 h-40 mx-auto rounded-2xl"
                />
              </div>
            </div>

            {/* Main Title */}
            <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 dark:from-white dark:via-slate-200 dark:to-white bg-clip-text text-transparent mb-6 leading-tight">
              Take Control of Your
              <br />
              <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Financial Future
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto mb-12 leading-relaxed">
              Transform your financial habits with intelligent budgeting,
              automated categorization, and actionable insights that help you
              save more.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button
                onClick={handleDemoLogin}
                disabled={isLoggingIn}
                className="group relative px-8 py-4 bg-primary text-primary-foreground font-semibold rounded-2xl hover:bg-primary/90 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                <span className="flex items-center gap-2">
                  {isLoggingIn ? 'Logging in...' : 'Try Demo'}
                  {!isLoggingIn && (
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  )}
                </span>
              </button>

              <Link
                to="/login"
                className="px-8 py-4 bg-secondary text-secondary-foreground font-semibold rounded-2xl border border-transparent hover:bg-secondary/90 transition-all duration-300 transform hover:scale-105"
              >
                Sign In
              </Link>
            </div>

            {/* Error Message */}
            {loginError && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
                <p className="text-red-600 dark:text-red-400 text-center">
                  {loginError}
                </p>
              </div>
            )}
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            <div className="group relative p-8 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50 rounded-3xl hover:bg-white/80 dark:hover:bg-slate-900/80 transition-all duration-300 transform hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/10 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/90 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                  Smart Analytics
                </h3>
                <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                  Get AI-powered insights into your spending patterns with
                  interactive charts and personalized recommendations.
                </p>
              </div>
            </div>

            <div className="group relative p-8 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50 rounded-3xl hover:bg-white/80 dark:hover:bg-slate-900/80 transition-all duration-300 transform hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                  Secure & Private
                </h3>
                <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                  Bank-level security protects your financial data with
                  end-to-end encryption and privacy-first design.
                </p>
              </div>
            </div>

            <div className="group relative p-8 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50 rounded-3xl hover:bg-white/80 dark:hover:bg-slate-900/80 transition-all duration-300 transform hover:scale-105">
              <div className="absolute inset-0 bg-gradient-to-br from-secondary/10 to-pink-500/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <div className="w-12 h-12 bg-gradient-to-br from-secondary to-pink-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                  Automated Budgeting
                </h3>
                <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                  Set smart budgets that adapt to your lifestyle with automatic
                  categorization and spending alerts.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
