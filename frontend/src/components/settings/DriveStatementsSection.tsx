import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  driveStatementsApi,
  type DriveStatus,
  type PickerTokenResponse,
} from '@/lib/api/driveStatements';
import {
  CheckCircle2,
  Cloud,
  FolderOpen,
  Loader2,
  Unlink,
  Unplug,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

interface PickerDocument {
  id: string;
  name: string;
}

interface PickerResponse {
  action: string;
  docs?: PickerDocument[];
}

interface PickerView {
  setSelectFolderEnabled(value: boolean): PickerView;
  setMimeTypes(value: string): PickerView;
}

interface PickerBuilder {
  addView(view: PickerView): PickerBuilder;
  setOAuthToken(token: string): PickerBuilder;
  setDeveloperKey(key: string): PickerBuilder;
  setAppId(appId: string): PickerBuilder;
  setCallback(callback: (data: PickerResponse) => void): PickerBuilder;
  build(): { setVisible(value: boolean): void };
}

interface PickerNamespace {
  Action: { PICKED: string };
  ViewId: { FOLDERS: string };
  DocsView: new (viewId: string) => PickerView;
  PickerBuilder: new () => PickerBuilder;
}

declare global {
  interface Window {
    gapi?: { load: (api: string, callback: () => void) => void };
    google?: { picker?: PickerNamespace };
  }
}

const FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder';

export function DriveStatementsSection() {
  const [status, setStatus] = useState<DriveStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [showUnlinkConfirm, setShowUnlinkConfirm] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  const loadStatus = async () => {
    setLoading(true);
    try {
      setStatus(await driveStatementsApi.getStatus());
    } catch (error) {
      toast.error('Unable to load Drive statement settings', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadStatus();
  }, []);

  useEffect(() => {
    const connected = searchParams.get('drive') === 'connected';
    const driveError = searchParams.get('drive_error');
    if (connected) {
      toast.success('Google Drive connected');
      searchParams.delete('drive');
      setSearchParams(searchParams, { replace: true });
      void loadStatus();
    } else if (driveError) {
      toast.error('Google Drive connection failed', {
        description: driveError,
      });
      searchParams.delete('drive_error');
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const connectDrive = async () => {
    setBusy(true);
    try {
      const { auth_url } = await driveStatementsApi.startOAuth();
      window.location.assign(auth_url);
    } catch (error) {
      toast.error('Unable to start Google Drive connection', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
      setBusy(false);
    }
  };

  const chooseFolder = async () => {
    setBusy(true);
    try {
      const pickerToken = await driveStatementsApi.getPickerToken();
      await loadGooglePicker();
      openPicker(pickerToken, async folder => {
        try {
          const response = await driveStatementsApi.activate({
            folderId: folder.id,
            folderName: folder.name,
          });
          setStatus(response.status);
          toast.success('Google Drive statement storage activated', {
            description: `${response.account_folders_created} account folders created, ${response.statements_migrated} statements migrated.`,
          });
          if (response.errors.length > 0) {
            toast.warning('Some statements could not be migrated', {
              description: response.errors[0],
            });
          }
        } catch (error) {
          toast.error('Unable to activate Drive folder', {
            description:
              error instanceof Error ? error.message : 'Please try again.',
          });
        } finally {
          setBusy(false);
        }
      });
    } catch (error) {
      toast.error('Unable to open Google Drive Picker', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
      setBusy(false);
    }
  };

  const disconnect = async () => {
    setBusy(true);
    try {
      setStatus(await driveStatementsApi.disconnect());
      toast.success('Google Drive disconnected');
    } catch (error) {
      toast.error('Unable to disconnect Google Drive', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setBusy(false);
    }
  };

  const unlinkFolder = async () => {
    setBusy(true);
    try {
      const response = await driveStatementsApi.deactivate();
      setStatus(response.status);
      setShowUnlinkConfirm(false);
      toast.success('Google Drive folder unlinked', {
        description: `${response.statements_migrated} statements moved back to local storage.`,
      });
      if (response.errors.length > 0) {
        toast.warning('Some statements could not be migrated', {
          description: response.errors[0],
        });
      }
    } catch (error) {
      toast.error('Unable to unlink Drive folder', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setBusy(false);
    }
  };

  const isConnected = Boolean(status?.connected);
  const isActive = Boolean(status?.active);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cloud className="h-5 w-5" />
          Statement Storage
        </CardTitle>
        <CardDescription>
          Sync statements to an empty Google Drive folder. Richtato creates one
          flat folder per account.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading Drive settings...
          </div>
        ) : (
          <>
            <div className="rounded-lg border border-border bg-muted/20 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={isActive ? 'default' : 'outline'}>
                  {isActive
                    ? 'Drive active'
                    : isConnected
                      ? 'Connected'
                      : 'Not connected'}
                </Badge>
                {!status?.configured && (
                  <Badge variant="destructive">OAuth not configured</Badge>
                )}
              </div>
              <div className="mt-3 space-y-1 text-sm text-muted-foreground">
                {status?.google_account_email && (
                  <p>Google account: {status.google_account_email}</p>
                )}
                {status?.root_folder_name && (
                  <p className="flex items-center gap-2">
                    <FolderOpen className="h-4 w-4" />
                    Root folder: {status.root_folder_name}
                  </p>
                )}
                {isActive && (
                  <p>
                    {status?.account_folders.length ?? 0} account folders
                    managed in Drive.
                  </p>
                )}
                {status?.last_error && (
                  <p className="text-destructive">{status.last_error}</p>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {!isConnected && (
                <Button
                  onClick={connectDrive}
                  disabled={busy || !status?.configured}
                >
                  {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Connect Google Drive
                </Button>
              )}
              {isConnected && !isActive && (
                <Button onClick={chooseFolder} disabled={busy}>
                  {busy ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                  )}
                  Choose Empty Folder
                </Button>
              )}
              {isConnected && !isActive && (
                <Button variant="outline" onClick={disconnect} disabled={busy}>
                  <Unplug className="mr-2 h-4 w-4" />
                  Disconnect
                </Button>
              )}
              {isActive && (
                <Button
                  variant="outline"
                  onClick={() => setShowUnlinkConfirm(true)}
                  disabled={busy}
                >
                  <Unlink className="mr-2 h-4 w-4" />
                  Unlink Folder
                </Button>
              )}
            </div>
            <AlertDialog
              open={showUnlinkConfirm}
              onOpenChange={setShowUnlinkConfirm}
            >
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>
                    Unlink Google Drive folder?
                  </AlertDialogTitle>
                  <AlertDialogDescription>
                    Statement files will move back to local storage and accounts
                    will stop syncing to Drive. Your Google account stays
                    connected so you can choose a different folder later.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel disabled={busy}>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={event => {
                      event.preventDefault();
                      void unlinkFolder();
                    }}
                    disabled={busy}
                  >
                    {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Unlink Folder
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function loadGooglePicker(): Promise<void> {
  return loadScript('https://apis.google.com/js/api.js', 'google-api-js').then(
    () =>
      new Promise((resolve, reject) => {
        if (!window.gapi) {
          reject(new Error('Google API script did not load.'));
          return;
        }
        window.gapi.load('picker', resolve);
      })
  );
}

function loadScript(src: string, id: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.getElementById(id);
    if (existing) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.id = id;
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.body.appendChild(script);
  });
}

function openPicker(
  pickerToken: PickerTokenResponse,
  onPicked: (folder: PickerDocument) => void
) {
  const picker = window.google?.picker;
  if (!picker) {
    throw new Error('Google Picker is not available.');
  }
  if (!pickerToken.developer_key) {
    throw new Error('Google Drive Picker API key is not configured.');
  }

  const view = new picker.DocsView(picker.ViewId.FOLDERS)
    .setSelectFolderEnabled(true)
    .setMimeTypes(FOLDER_MIME_TYPE);
  const builder = new picker.PickerBuilder()
    .addView(view)
    .setOAuthToken(pickerToken.access_token)
    .setDeveloperKey(pickerToken.developer_key)
    .setCallback(data => {
      if (data.action === picker.Action.PICKED && data.docs?.[0]) {
        onPicked(data.docs[0]);
      }
    });

  if (pickerToken.app_id) {
    builder.setAppId(pickerToken.app_id);
  }

  builder.build().setVisible(true);
}
