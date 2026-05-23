import { AppearanceSection } from '@/components/settings/AppearanceSection';
import { DriveStatementsSection } from '@/components/settings/DriveStatementsSection';
import { NotificationsSection } from '@/components/settings/NotificationsSection';

export function Preferences() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-1">
        <DriveStatementsSection />
        <AppearanceSection />
        <NotificationsSection />
      </div>
    </div>
  );
}
