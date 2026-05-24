import { AppearanceSection } from '@/components/settings/AppearanceSection';
import { NotificationsSection } from '@/components/settings/NotificationsSection';
import { ProfileSection } from '@/components/settings/ProfileSection';

export function Preferences() {
  return (
    <div className="space-y-6">
      <ProfileSection />
      <AppearanceSection />
      <NotificationsSection />
    </div>
  );
}
