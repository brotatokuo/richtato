import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Bell, Database, Palette, Shield } from 'lucide-react';
import { useState } from 'react';

export function Settings() {
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      weekly: true,
      monthly: true,
    },
    privacy: {
      dataSharing: false,
      analytics: true,
      marketing: false,
    },
    appearance: {
      theme: 'system',
      currency: 'USD',
      dateFormat: 'MM/DD/YYYY',
    },
    data: {
      autoBackup: true,
      retentionPeriod: '2',
    },
  });

  const handleNotificationChange = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: value,
      },
    }));
  };

  const handlePrivacyChange = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      privacy: {
        ...prev.privacy,
        [key]: value,
      },
    }));
  };

  const handleAppearanceChange = (key: string, value: string) => {
    setSettings(prev => ({
      ...prev,
      appearance: {
        ...prev.appearance,
        [key]: value,
      },
    }));
  };

  const handleDataChange = (key: string, value: string | boolean) => {
    setSettings(prev => ({
      ...prev,
      data: {
        ...prev.data,
        [key]: value,
      },
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account preferences and application settings
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notifications
            </CardTitle>
            <CardDescription>
              Configure how you receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="email-notifications">Email Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive updates via email
                </p>
              </div>
              <Switch
                id="email-notifications"
                checked={settings.notifications.email}
                onCheckedChange={checked =>
                  handleNotificationChange('email', checked)
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="push-notifications">Push Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive browser notifications
                </p>
              </div>
              <Switch
                id="push-notifications"
                checked={settings.notifications.push}
                onCheckedChange={checked =>
                  handleNotificationChange('push', checked)
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="weekly-reports">Weekly Reports</Label>
                <p className="text-sm text-muted-foreground">
                  Get weekly spending summaries
                </p>
              </div>
              <Switch
                id="weekly-reports"
                checked={settings.notifications.weekly}
                onCheckedChange={checked =>
                  handleNotificationChange('weekly', checked)
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="monthly-reports">Monthly Reports</Label>
                <p className="text-sm text-muted-foreground">
                  Get monthly financial summaries
                </p>
              </div>
              <Switch
                id="monthly-reports"
                checked={settings.notifications.monthly}
                onCheckedChange={checked =>
                  handleNotificationChange('monthly', checked)
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Privacy */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Privacy & Security
            </CardTitle>
            <CardDescription>
              Control your data and privacy settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="data-sharing">Data Sharing</Label>
                <p className="text-sm text-muted-foreground">
                  Allow anonymous usage data collection
                </p>
              </div>
              <Switch
                id="data-sharing"
                checked={settings.privacy.dataSharing}
                onCheckedChange={checked =>
                  handlePrivacyChange('dataSharing', checked)
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="analytics">Analytics</Label>
                <p className="text-sm text-muted-foreground">
                  Help improve the app with usage analytics
                </p>
              </div>
              <Switch
                id="analytics"
                checked={settings.privacy.analytics}
                onCheckedChange={checked =>
                  handlePrivacyChange('analytics', checked)
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="marketing">Marketing</Label>
                <p className="text-sm text-muted-foreground">
                  Receive promotional emails and updates
                </p>
              </div>
              <Switch
                id="marketing"
                checked={settings.privacy.marketing}
                onCheckedChange={checked =>
                  handlePrivacyChange('marketing', checked)
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              Appearance
            </CardTitle>
            <CardDescription>
              Customize the look and feel of the application
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="theme">Theme</Label>
              <Select
                value={settings.appearance.theme}
                onValueChange={value => handleAppearanceChange('theme', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="currency">Currency</Label>
              <Select
                value={settings.appearance.currency}
                onValueChange={value =>
                  handleAppearanceChange('currency', value)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD ($)</SelectItem>
                  <SelectItem value="EUR">EUR (€)</SelectItem>
                  <SelectItem value="GBP">GBP (£)</SelectItem>
                  <SelectItem value="CAD">CAD (C$)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="date-format">Date Format</Label>
              <Select
                value={settings.appearance.dateFormat}
                onValueChange={value =>
                  handleAppearanceChange('dateFormat', value)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                  <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                  <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Data Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Data Management
            </CardTitle>
            <CardDescription>
              Manage your data and backup settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="auto-backup">Auto Backup</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically backup your data
                </p>
              </div>
              <Switch
                id="auto-backup"
                checked={settings.data.autoBackup}
                onCheckedChange={checked =>
                  handleDataChange('autoBackup', checked)
                }
              />
            </div>

            <div>
              <Label htmlFor="retention">Data Retention</Label>
              <Select
                value={settings.data.retentionPeriod}
                onValueChange={value =>
                  handleDataChange('retentionPeriod', value)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 Year</SelectItem>
                  <SelectItem value="2">2 Years</SelectItem>
                  <SelectItem value="5">5 Years</SelectItem>
                  <SelectItem value="forever">Forever</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="pt-4 space-y-2">
              <Button variant="outline" className="w-full">
                Export Data
              </Button>
              <Button variant="outline" className="w-full">
                Import Data
              </Button>
              <Button variant="destructive" className="w-full">
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
