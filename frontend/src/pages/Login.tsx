import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';
import { Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-foreground">Sign In</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Log in to Richtato
          </p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <div className="relative mt-1">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="pr-10"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 dark:bg-red-950/20 p-3 rounded">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Log In'}
          </Button>
        </form>

        <div className="text-center space-y-2">
          <p className="text-sm text-muted-foreground">
            Not on Richtato?{' '}
            <Link to="/register" className="text-primary hover:underline">
              Create an account
            </Link>
          </p>
          <p className="text-sm text-muted-foreground">
            <Link to="/password-reset" className="text-primary hover:underline">
              Forgot password?
            </Link>
          </p>
          <p className="text-sm text-muted-foreground">
            <Link to="/welcome" className="text-primary hover:underline">
              ← Back to Welcome
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
