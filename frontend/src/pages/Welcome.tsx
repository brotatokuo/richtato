import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Welcome() {
  const { login } = useAuth();

  const handleDemoLogin = () => {
    // Demo login functionality
    login('demo', 'demopassword123!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="welcome-center max-w-4xl mx-auto text-center">
        {/* Logo Section */}
        <div className="gif-container mb-8">
          <img
            src="/richtato.png"
            alt="Richtato Logo"
            className="w-32 h-32 mx-auto animate-pulse"
            id="growth-gif"
          />
        </div>

        {/* Typewriter Effect Title */}
        <div className="typewriter mb-8">
          <div className="typewriter-text welcome-title text-4xl md:text-6xl font-bold text-gray-800 mb-4">
            Save with Richtato!
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="cta-buttons flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Link
            to="/login"
            className="cta-button secondary bg-white text-blue-600 border-2 border-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors duration-200"
          >
            Sign In
          </Link>
          <button
            onClick={handleDemoLogin}
            className="cta-button demo bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200"
          >
            Try Demo
          </button>
        </div>

        {/* Feature Grid */}
        <div className="feature-grid grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="feature-card bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300">
            <div className="feature-icon text-4xl text-blue-600 mb-4">
              <i className="fa-solid fa-cloud-arrow-up"></i>
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3">
              Smart Upload
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Upload bank statements from your bank. Our AI automatically
              categorizes your transactions.
            </p>
          </div>

          <div className="feature-card bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300">
            <div className="feature-icon text-4xl text-green-600 mb-4">
              <i className="fa-solid fa-chart-line"></i>
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3">
              Advanced Analytics
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Get powerful insights with interactive charts and detailed
              breakdowns.
            </p>
          </div>

          <div className="feature-card bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300">
            <div className="feature-icon text-4xl text-purple-600 mb-4">
              <i className="fa-solid fa-piggy-bank"></i>
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3">
              Budget Management
            </h3>
            <p className="text-gray-600 leading-relaxed">
              Set budgets, track your progress, and understand your money.
            </p>
          </div>
        </div>
      </div>

      {/* Add Font Awesome for icons */}
      <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
      />
    </div>
  );
}
