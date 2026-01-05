import {
  ArrowRight,
  BarChart3,
  Building2,
  ChevronRight,
  FileText,
  GitBranch,
  Link2,
  PiggyBank,
  Quote,
  Shield,
  Sparkles,
  Star,
  Target,
  TrendingUp,
  Wallet,
  Zap,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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

// Bank logos
const bankLogos = [
  { name: 'Chase', src: '/images/logos/chase.webp' },
  { name: 'American Express', src: '/images/logos/amex.png' },
  { name: 'Bank of America', src: '/images/logos/bofa.png' },
  { name: 'Citi', src: '/images/logos/citi.webp' },
  { name: 'Wells Fargo', src: '/images/logos/wells_fargo.png' },
  { name: 'Charles Schwab', src: '/images/logos/charles_schwab.png' },
  { name: 'Fidelity', src: '/images/logos/fidelity.png' },
  { name: 'Marcus', src: '/images/logos/marcus.png' },
  { name: 'Robinhood', src: '/images/logos/robinhood.png' },
  { name: 'SoFi', src: '/images/logos/sofi.png' },
];

// Testimonials
const testimonials = [
  {
    quote:
      "Finally, a finance app that doesn't feel like a spreadsheet. The Sankey diagrams are incredible for understanding where my money actually goes.",
    author: 'Sarah K.',
    role: 'Product Designer',
    avatar: 'SK',
    rating: 5,
  },
  {
    quote:
      'The AI categorization saves me hours each month. It learned my patterns within a week and now I barely touch it.',
    author: 'Michael R.',
    role: 'Software Engineer',
    avatar: 'MR',
    rating: 5,
  },
  {
    quote:
      'Connecting all my bank accounts was seamless. I can finally see my complete financial picture in one place.',
    author: 'Emily T.',
    role: 'Freelance Consultant',
    avatar: 'ET',
    rating: 5,
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

// Stats
const stats = [
  { value: '12K+', label: 'Financial Institutions' },
  { value: '99.9%', label: 'Uptime' },
  { value: '256-bit', label: 'Encryption' },
  { value: 'SOC 2', label: 'Compliant' },
];

export function Welcome() {
  const { demoLogin } = useAuth();
  const navigate = useNavigate();
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
              <a
                href="#testimonials"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Testimonials
              </a>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                Sign In
              </Link>
              <button
                onClick={handleDemoLogin}
                disabled={isLoggingIn}
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all disabled:opacity-50"
              >
                {isLoggingIn ? 'Loading...' : 'Try Demo'}
              </button>
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
              className="px-8 py-4 bg-secondary/10 text-secondary-foreground font-semibold rounded-2xl border border-secondary/30 hover:bg-secondary/20 transition-all duration-300 transform hover:scale-105 flex items-center gap-2"
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

          {/* Stats row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-8 max-w-4xl mx-auto animate-fade-in-up animate-on-load [animation-delay:400ms]">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="p-4 rounded-2xl bg-card/50 backdrop-blur-sm border border-border/50"
              >
                <div className="text-2xl sm:text-3xl font-bold text-foreground mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
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

      {/* Bank Partners Section */}
      <section className="py-24 sm:py-32 bg-muted/30 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
              <Building2 className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary">
                Bank Integrations
              </span>
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold text-foreground mb-6">
              Connect with confidence
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Powered by Plaid, securely connect to over 12,000 financial
              institutions across North America.
            </p>
          </div>

          {/* Logo marquee */}
          <div className="relative">
            {/* Gradient masks */}
            <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-muted/30 to-transparent z-10 pointer-events-none" />
            <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-muted/30 to-transparent z-10 pointer-events-none" />

            {/* Scrolling logos */}
            <div className="flex overflow-hidden">
              <div className="flex items-center gap-12 animate-marquee">
                {[...bankLogos, ...bankLogos].map((bank, index) => (
                  <div
                    key={index}
                    className="flex-shrink-0 w-32 h-16 bg-card rounded-xl border border-border flex items-center justify-center p-4 hover:border-primary/30 transition-colors"
                  >
                    <img
                      src={bank.src}
                      alt={bank.name}
                      className="max-w-full max-h-full object-contain opacity-70 hover:opacity-100 transition-opacity"
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Security badges */}
          <div className="mt-16 flex flex-wrap justify-center gap-8">
            <div className="flex items-center gap-3 text-muted-foreground">
              <Shield className="w-6 h-6 text-primary" />
              <span>Bank-level encryption</span>
            </div>
            <div className="flex items-center gap-3 text-muted-foreground">
              <Shield className="w-6 h-6 text-primary" />
              <span>Read-only access</span>
            </div>
            <div className="flex items-center gap-3 text-muted-foreground">
              <Shield className="w-6 h-6 text-primary" />
              <span>SOC 2 Type II certified</span>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/10 border border-secondary/20 mb-6">
              <Quote className="w-4 h-4 text-secondary" />
              <span className="text-sm font-medium text-secondary">
                Testimonials
              </span>
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold text-foreground mb-6">
              Loved by people like you
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              See what our users have to say about transforming their financial
              habits.
            </p>
          </div>

          {/* Testimonial cards */}
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div
                key={index}
                className="relative p-8 bg-card rounded-3xl border border-border hover:border-primary/30 transition-all duration-300 hover:shadow-xl"
              >
                {/* Quote icon */}
                <Quote className="absolute top-6 right-6 w-10 h-10 text-primary/10" />

                {/* Rating */}
                <div className="flex gap-1 mb-6">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star
                      key={i}
                      className="w-5 h-5 fill-secondary text-secondary"
                    />
                  ))}
                </div>

                {/* Quote */}
                <p className="text-foreground mb-8 leading-relaxed">
                  "{testimonial.quote}"
                </p>

                {/* Author */}
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-semibold">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">
                      {testimonial.author}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {testimonial.role}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-24 sm:py-32 relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-background to-secondary/10" />

        {/* Floating elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-pulse-glow" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl animate-pulse-glow [animation-delay:1s]" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-bold text-foreground mb-8">
            Ready to take control of your
            <br />
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              financial future?
            </span>
          </h2>
          <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto">
            Join thousands of users who have transformed their relationship with
            money. Start your journey today.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleDemoLogin}
              disabled={isLoggingIn}
              className="group px-10 py-5 bg-primary text-primary-foreground font-semibold rounded-2xl hover:bg-primary/90 transition-all duration-300 transform hover:scale-105 hover:shadow-xl hover:shadow-primary/25 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoggingIn ? 'Loading...' : 'Start Free Demo'}
              {!isLoggingIn && (
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              )}
            </button>
            <Link
              to="/register"
              className="px-10 py-5 bg-card text-foreground font-semibold rounded-2xl border border-border hover:border-primary/50 hover:bg-muted transition-all duration-300 transform hover:scale-105"
            >
              Create Free Account
            </Link>
          </div>

          <p className="mt-8 text-sm text-muted-foreground">
            No credit card required. Free to use forever for basic features.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 border-t border-border bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <img
                  src="/richtato.png"
                  alt="Richtato"
                  className="w-10 h-10 rounded-xl"
                />
                <span className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                  Richtato
                </span>
              </div>
              <p className="text-muted-foreground max-w-md mb-6">
                The modern way to manage your personal finances. Connect your
                accounts, track your spending, and build wealth with intelligent
                insights.
              </p>
              <div className="flex gap-4">
                <a
                  href="#"
                  className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
                >
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" />
                  </svg>
                </a>
                <a
                  href="#"
                  className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
                >
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Links */}
            <div>
              <h4 className="font-semibold text-foreground mb-4">Product</h4>
              <ul className="space-y-3">
                <li>
                  <a
                    href="#features"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    href="#showcase"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Product Tour
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Security
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-foreground mb-4">Company</h4>
              <ul className="space-y-3">
                <li>
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    About
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Blog
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Terms of Service
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="mt-16 pt-8 border-t border-border flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} Richtato. All rights reserved.
            </p>
            <p className="text-sm text-muted-foreground">
              Made with ❤️ for your financial success
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
