import { AppearanceSection } from '@/components/settings/AppearanceSection';
import { NotificationsSection } from '@/components/settings/NotificationsSection';
import { ProfileSection } from '@/components/settings/ProfileSection';

function SettingsGroup({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          {title}
        </h2>
        {description ? (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {children}
    </section>
  );
}

export function Preferences() {
  return (
    <div className="w-full max-w-5xl space-y-8">
      <SettingsGroup
        title="Account & display"
        description="Profile details and how amounts, dates, and themes appear across the app."
      >
        <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
          <ProfileSection />
          <AppearanceSection />
        </div>
      </SettingsGroup>

      <SettingsGroup
        title="Notifications"
        description="Choose how Richtato alerts you about bank sync and account activity."
      >
        <NotificationsSection />
      </SettingsGroup>
    </div>
  );
}
