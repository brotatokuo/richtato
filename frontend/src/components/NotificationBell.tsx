import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  type InAppNotification,
  notificationsApi,
} from '@/lib/api/notifications';
import { Bell, CheckCheck } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

export function NotificationBell() {
  const [notifications, setNotifications] = useState<InAppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const loadNotifications = useCallback(async () => {
    try {
      const payload = await notificationsApi.list({ limit: 10 });
      setNotifications(payload.notifications);
      setUnreadCount(payload.unread_count);
    } catch {
      // Header notifications should not block the page.
    }
  }, []);

  useEffect(() => {
    void loadNotifications();
  }, [loadNotifications]);

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllRead();
      await loadNotifications();
    } catch (error) {
      toast.error('Unable to mark notifications read', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    }
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge className="absolute -right-1 -top-1 h-5 min-w-5 justify-center rounded-full px-1 text-[10px]">
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
          <span className="sr-only">Notifications</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-0">
        <div className="flex items-center justify-between border-b border-border px-3 py-2">
          <p className="text-sm font-medium">Notifications</p>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-1 text-xs"
            onClick={() => void handleMarkAllRead()}
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Mark read
          </Button>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {notifications.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">
              No notifications yet.
            </p>
          ) : (
            notifications.map(notification => (
              <NotificationRow
                key={notification.id}
                notification={notification}
                onMarkedRead={loadNotifications}
              />
            ))
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

function NotificationRow({
  notification,
  onMarkedRead,
}: {
  notification: InAppNotification;
  onMarkedRead: () => void;
}) {
  const content = (
    <div className="block border-b border-border px-3 py-3 text-left last:border-b-0 hover:bg-muted/50">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium">{notification.title}</p>
        {!notification.read_at && (
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
        )}
      </div>
      {notification.body && (
        <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">
          {notification.body}
        </p>
      )}
    </div>
  );

  const markRead = async () => {
    if (notification.read_at) return;
    await notificationsApi.markRead(notification.id);
    onMarkedRead();
  };

  if (notification.action_url) {
    return (
      <Link to={notification.action_url} onClick={() => void markRead()}>
        {content}
      </Link>
    );
  }

  return (
    <button className="w-full" onClick={() => void markRead()}>
      {content}
    </button>
  );
}
