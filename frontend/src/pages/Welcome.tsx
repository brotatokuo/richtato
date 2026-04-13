import {
  ArrowRight,
  BarChart3,
  ChevronRight,
  FileText,
  GitBranch,
  Link2,
  Moon,
  PiggyBank,
  Sparkles,
  Sun,
  Target,
  TrendingUp,
  Wallet,
  Zap,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/useTheme';
import { useAuth } from '../hooks/useAuth';

// Feature data
const features = [
  {
    icon: Link2,
    title: 'Bank Sync',
    description:
      'Connect 12,000+ financial institutions with Plaid. Your accounts sync automatically.',
    gradient: 'from-emerald-500 to-teal-600',
    delay: 'delay-100',
  },
  {
    icon: GitBranch,
    title: 'Cashflow Visualization',
    description:
      'Interactive Sankey diagrams show exactly where your money flows each month.',
    gradient: 'from-blue-500 to-indigo-600',
    delay: 'delay-200',
  },
  {
    icon: Sparkles,
    title: 'AI Categorization',
    description:
      'OpenAI-powered auto-categorization learns your spending patterns.',
    gradient: 'from-violet-500 to-purple-600',
    delay: 'delay-300',
  },
  {
    icon: Target,
    title: 'Smart Budgets',
    description:
      'Set intelligent budgets with real-time alerts when you approach limits.',
    gradient: 'from-amber-500 to-orange-600',
    delay: 'delay-400',
  },
  {
    icon: TrendingUp,
    title: 'Net Worth Tracking',
    description:
      'Track assets and liabilities across all accounts in one dashboard.',
    gradient: 'from-pink-500 to-rose-600',
    delay: 'delay-500',
  },
  {
    icon: FileText,
    title: 'Annual Reports',
    description:
      'Year-end financial analysis with essential vs non-essential breakdowns.',
    gradient: 'from-cyan-500 to-sky-600',
    delay: 'delay-600',
  },
];

// Showcase data
const showcases = [
  {
    title: 'Budget Dashboard',
    description:
      'Track spending by category with beautiful pie charts and progress bars. Know exactly where every dollar goes.',
    image: '/images/mockups/mockup-budget.svg',
    features: [
      'Category breakdown',
      'Progress tracking',
      'Monthly comparisons',
    ],
  },
  {
    title: 'Cashflow Sankey',
    description:
      'Visualize your entire money flow from income sources through expenses to savings with interactive Sankey diagrams.',
    image: '/images/mockups/mockup-cashflow.svg',
    features: ['Income tracking', 'Expense flows', 'Savings visualization'],
  },
  {
    title: 'Net Worth Tracker',
    description:
      'Watch your wealth grow over time with comprehensive asset and liability tracking across all your accounts.',
    image: '/images/mockups/mockup-assets.svg',
    features: ['Asset allocation', 'Growth trends', 'Account aggregation'],
  },
];

export function Welcome() {
  const { demoLogin } = useAuth();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [activeShowcase, setActiveShowcase] = useState(0);
  const heroRef = useRef<HTMLDivElement>(null);

  // Auto-rotate showcase
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveShowcase(prev => (prev + 1) % showcases.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDemoLogin = async () => {
    try {
      setIsLoggingIn(true);
      setLoginError(null);
      await demoLogin();
      navigate('/report');
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
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <img
                src="/richtato.png"
                alt="Richtato"
                className="w-10 h-10 rounded-xl"
              />
              <span className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                Richtato
              </span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a
                href="#features"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Features
              </a>
              <a
                href="#showcase"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Product
              </a>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
              >
                {theme === 'light' ? (
                  <Moon className="w-5 h-5" />
                ) : (
                  <Sun className="w-5 h-5" />
                )}
              </button>
              <Link
                to="/login"
                className="px-4 py-2 text-sm font-medium text-primary hover:bg-primary/10 rounded-lg transition-colors"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden"
      >
        {/* Animated background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/5" />

        {/* Floating shapes */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary/10 rounded-full blur-3xl hero-float-1" />
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl hero-float-2" />
          <div className="absolute bottom-1/4 left-1/3 w-64 h-64 bg-accent/10 rounded-full blur-3xl hero-float-3" />

          {/* Decorative icons floating */}
          <div className="absolute top-1/4 right-[15%] animate-float opacity-20">
            <BarChart3 className="w-16 h-16 text-primary" />
          </div>
          <div className="absolute bottom-1/3 left-[10%] animate-float-slow opacity-20">
            <PiggyBank className="w-20 h-20 text-secondary" />
          </div>
          <div className="absolute top-1/2 right-[10%] animate-float opacity-15">
            <Wallet className="w-14 h-14 text-accent" />
          </div>
        </div>

        <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8 animate-fade-in-down">
            <Sparkles className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">
              AI-Powered Finance Management
            </span>
          </div>

          {/* Main headline */}
          <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold mb-8 leading-tight animate-fade-in-up animate-on-load [animation-delay:100ms]">
            <span className="block text-foreground">Your Money,</span>
            <span className="block bg-gradient-to-r from-primary via-emerald-400 to-secondary bg-clip-text text-transparent animated-gradient bg-[length:200%_auto]">
              Visualized
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-xl sm:text-2xl text-muted-foreground max-w-3xl mx-auto mb-12 leading-relaxed animate-fade-in-up animate-on-load [animation-delay:200ms]">
            Connect your banks, visualize your cashflow with beautiful Sankey
            diagrams, and let AI categorize your transactions. Take control of
            your financial future.
          </p>

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16 animate-fade-in-up animate-on-load [animation-delay:300ms]">
            <button
              onClick={handleDemoLogin}
              disabled={isLoggingIn}
              className="group relative px-8 py-4 bg-primary text-primary-foreground font-semibold rounded-2xl hover:bg-primary/90 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-primary/25 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center gap-2"
            >
              {isLoggingIn ? (
                'Logging in...'
              ) : (
                <>
                  Try Demo Free
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>

            <Link
              to="/register"
              className="px-8 py-4 bg-secondary text-secondary-foreground font-semibold rounded-2xl hover:bg-secondary/90 transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
            >
              Create Account
              <ChevronRight className="w-5 h-5" />
            </Link>
          </div>

          {/* Error message */}
          {loginError && (
            <div className="max-w-md mx-auto p-4 bg-destructive/10 border border-destructive/30 rounded-xl mb-8 animate-fade-in">
              <p className="text-destructive text-center">{loginError}</p>
            </div>
          )}

        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 rounded-full border-2 border-muted-foreground/30 flex items-start justify-center p-1">
            <div className="w-1.5 h-3 bg-muted-foreground/50 rounded-full animate-pulse" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 sm:py-32 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section header */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
              <Zap className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary">
                Powerful Features
              </span>
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold text-foreground mb-6">
              Everything you need to
              <br />
              <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                master your finances
              </span>
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              From automatic bank syncing to AI-powered insights, we've built
              the tools you need to take control.
            </p>
          </div>

          {/* Features grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group relative p-8 bg-card rounded-3xl border border-border hover:border-primary/50 transition-all duration-500 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1"
              >
                {/* Gradient glow on hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-secondary/5 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                <div className="relative z-10">
                  {/* Icon */}
                  <div
                    className={`w-14 h-14 bg-gradient-to-br ${feature.gradient} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}
                  >
                    <feature.icon className="w-7 h-7 text-white" />
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-bold text-foreground mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* App Showcase Section */}
      <section id="showcase" className="py-24 sm:py-32 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section header */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/10 border border-secondary/20 mb-6">
              <BarChart3 className="w-4 h-4 text-secondary" />
              <span className="text-sm font-medium text-secondary">
                Product Tour
              </span>
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold text-foreground mb-6">
              See it in action
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Beautiful dashboards that make managing money actually enjoyable.
            </p>
          </div>

          {/* Showcase tabs */}
          <div className="flex flex-wrap justify-center gap-4 mb-12">
            {showcases.map((showcase, index) => (
              <button
                key={index}
                onClick={() => setActiveShowcase(index)}
                className={`px-6 py-3 rounded-full font-medium transition-all duration-300 ${
                  activeShowcase === index
                    ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/25'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {showcase.title}
              </button>
            ))}
          </div>

          {/* Showcase content */}
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Image */}
            <div className="relative order-2 lg:order-1">
              <div className="relative rounded-2xl overflow-hidden shadow-2xl shadow-black/20 border border-border">
                <img
                  src={showcases[activeShowcase].image}
                  alt={showcases[activeShowcase].title}
                  className="w-full h-auto transition-opacity duration-500"
                />
                {/* Gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-background/20 to-transparent pointer-events-none" />
              </div>

              {/* Decorative elements */}
              <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-primary/20 rounded-full blur-2xl" />
              <div className="absolute -top-4 -left-4 w-24 h-24 bg-secondary/20 rounded-full blur-2xl" />
            </div>

            {/* Description */}
            <div className="order-1 lg:order-2">
              <h3 className="text-3xl sm:text-4xl font-bold text-foreground mb-6">
                {showcases[activeShowcase].title}
              </h3>
              <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
                {showcases[activeShowcase].description}
              </p>

              {/* Feature list */}
              <ul className="space-y-4 mb-8">
                {showcases[activeShowcase].features.map((feature, index) => (
                  <li key={index} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                      <ChevronRight className="w-4 h-4 text-primary" />
                    </div>
                    <span className="text-foreground">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={handleDemoLogin}
                disabled={isLoggingIn}
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-medium rounded-xl hover:bg-primary/90 transition-all disabled:opacity-50"
              >
                Try it now
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
