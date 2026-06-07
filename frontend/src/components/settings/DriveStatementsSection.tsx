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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useDrive } from '@/contexts/DriveContext';
import { usePlatformTour } from '@/contexts/PlatformTourContext';
import {
  driveStatementsApi,
  type DriveAdoptPreview,
  type PickerTokenResponse,
} from '@/lib/api/driveStatements';
import {
  Cloud,
  FolderInput,
  FolderOpen,
  FolderPlus,
  FolderSync,
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

type ActivationMode = 'create' | 'adopt';

export function DriveStatementsSection() {
  const {
    driveStatus: status,
    isLoading: loading,
    refreshDriveStatus,
  } = useDrive();
  const { markOAuthResume, isRunning: isTourRunning } = usePlatformTour();
  const [busy, setBusy] = useState(false);
  const [showUnlinkConfirm, setShowUnlinkConfirm] = useState(false);
  const [adoptPreview, setAdoptPreview] = useState<DriveAdoptPreview | null>(
    null
  );
  const [pendingAdoptFolder, setPendingAdoptFolder] =
    useState<PickerDocument | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const connected = searchParams.get('drive') === 'connected';
    const driveError = searchParams.get('drive_error');
    if (connected) {
      toast.success('Google Drive connected');
      searchParams.delete('drive');
      setSearchParams(searchParams, { replace: true });
      void refreshDriveStatus();
    } else if (driveError) {
      toast.error('Google Drive connection failed', {
        description: driveError,
      });
      searchParams.delete('drive_error');
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams, refreshDriveStatus]);

  const connectDrive = async () => {
    if (isTourRunning) {
      markOAuthResume();
    }
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

  const activateFolder = async (
    folder: PickerDocument,
    mode: ActivationMode
  ) => {
    try {
      const response = await driveStatementsApi.activate({
        folderId: folder.id,
        folderName: folder.name,
        adoptExisting: mode === 'adopt',
      });
      await refreshDriveStatus();
      setAdoptPreview(null);
      setPendingAdoptFolder(null);

      if (mode === 'adopt') {
        const adopted = response.account_folders_adopted;
        const created = response.account_folders_created;
        const imported = response.scan_summary?.files_imported ?? 0;
        toast.success('Existing Google Drive folders linked', {
          description: `${adopted} adopted, ${created} created, ${imported} statement file${imported === 1 ? '' : 's'} imported.`,
        });
        if (response.unmatched_drive_folders.length > 0) {
          toast.warning('Some Drive folders were not linked', {
            description: `${response.unmatched_drive_folders.length} folder${response.unmatched_drive_folders.length === 1 ? '' : 's'} did not match an active account.`,
          });
        }
      } else {
        toast.success('Google Drive statement storage activated', {
          description: `${response.account_folders_created} account folders created.`,
        });
      }

      if (response.errors.length > 0) {
        toast.warning('Some account folders could not be configured', {
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
  };

  const chooseFolder = async (mode: ActivationMode) => {
    setBusy(true);
    try {
      const pickerToken = await driveStatementsApi.getPickerToken();
      await loadGooglePicker();
      openPicker(pickerToken, async folder => {
        if (mode === 'create') {
          try {
            await activateFolder(folder, mode);
          } catch {
            setBusy(false);
          }
          return;
        }

        try {
          const preview = await driveStatementsApi.adoptPreview(folder.id);
          if (preview.errors.length > 0) {
            toast.error('Unable to use this Drive folder', {
              description: preview.errors[0]?.message ?? 'Please try again.',
            });
            setBusy(false);
            return;
          }
          setPendingAdoptFolder(folder);
          setAdoptPreview(preview);
        } catch (error) {
          toast.error('Unable to preview Drive folder', {
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

  const confirmAdopt = async () => {
    if (!pendingAdoptFolder) {
      return;
    }
    setBusy(true);
    await activateFolder(pendingAdoptFolder, 'adopt');
  };

  const disconnect = async () => {
    setBusy(true);
    try {
      await driveStatementsApi.disconnect();
      await refreshDriveStatus();
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
      await refreshDriveStatus();
      setShowUnlinkConfirm(false);
      toast.success('Google Drive folder unlinked', {
        description: `${response.account_folders_removed} account folders unlinked.`,
      });
      if (response.errors.length > 0) {
        toast.warning('Some account folders could not be unlinked', {
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

  const syncFolders = async () => {
    setBusy(true);
    try {
      const response = await driveStatementsApi.syncMissingFolders();
      await refreshDriveStatus();
      toast.success(
        `${response.account_folders_created} folder${response.account_folders_created === 1 ? '' : 's'} synced to Google Drive`
      );
      if (response.errors.length > 0) {
        toast.warning('Some folders could not be created', {
          description: response.errors[0],
        });
      }
    } catch (error) {
      toast.error('Unable to sync Drive folders', {
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setBusy(false);
    }
  };

  const isConnected = Boolean(status?.connected);
  const isActive = Boolean(status?.active);
  const missingFolderCount = status?.missing_folder_count ?? 0;

  return (
    <Card className="overflow-hidden">
      <CardHeader className="p-4 sm:p-6">
        <CardTitle className="flex items-center gap-2 text-xl sm:text-2xl">
          <Cloud className="h-5 w-5" />
          Statement Storage
        </CardTitle>
        <CardDescription>
          Sync statements to Google Drive. Choose an empty root folder to create
          a fresh structure, or link an existing Richtato-style root with{' '}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            {'{account_id}-{name}'}
          </code>{' '}
          subfolders.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 p-4 pt-0 sm:p-6 sm:pt-0">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading Drive settings...
          </div>
        ) : (
          <>
            <div
              className="rounded-lg border border-border bg-muted/20 p-3 sm:p-4"
              data-tour="drive-status"
            >
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
                  <p className="flex min-w-0 items-center gap-2">
                    <FolderOpen className="h-4 w-4 shrink-0" />
                    <span className="min-w-0 break-words">
                      Root folder: {status.root_folder_name}
                    </span>
                  </p>
                )}
                {isActive && (
                  <p>
                    {status?.account_folders.length ?? 0} account folders
                    managed in Drive.
                  </p>
                )}
                {isActive && missingFolderCount > 0 && (
                  <p className="text-amber-500">
                    {missingFolderCount} account
                    {missingFolderCount === 1 ? '' : 's'} missing a Drive
                    folder.
                  </p>
                )}
                {status?.last_error && (
                  <p className="text-destructive">{status.last_error}</p>
                )}
              </div>
            </div>

            <div
              className="grid gap-2 sm:flex sm:flex-wrap"
              data-tour="drive-folder-actions"
            >
              {!isConnected && (
                <Button
                  onClick={connectDrive}
                  disabled={busy || !status?.configured}
                  className="w-full sm:w-auto"
                  data-tour="drive-connect"
                >
                  {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Connect Google Drive
                </Button>
              )}
              {isConnected && !isActive && (
                <Button
                  onClick={() => void chooseFolder('create')}
                  disabled={busy}
                  className="w-full sm:w-auto"
                >
                  {busy ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FolderPlus className="mr-2 h-4 w-4" />
                  )}
                  Create New Structure
                </Button>
              )}
              {isConnected && !isActive && (
                <Button
                  variant="outline"
                  onClick={() => void chooseFolder('adopt')}
                  disabled={busy}
                  className="w-full sm:w-auto"
                >
                  {busy ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FolderInput className="mr-2 h-4 w-4" />
                  )}
                  Use Existing Folders
                </Button>
              )}
              {isConnected && !isActive && (
                <Button
                  variant="outline"
                  onClick={disconnect}
                  disabled={busy}
                  className="w-full sm:w-auto"
                >
                  <Unplug className="mr-2 h-4 w-4" />
                  Disconnect
                </Button>
              )}
              {isActive && missingFolderCount > 0 && (
                <Button
                  onClick={syncFolders}
                  disabled={busy}
                  className="w-full sm:w-auto"
                >
                  {busy ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FolderSync className="mr-2 h-4 w-4" />
                  )}
                  Sync Missing Folders ({missingFolderCount})
                </Button>
              )}
              {isActive && (
                <Button
                  variant="outline"
                  onClick={() => setShowUnlinkConfirm(true)}
                  disabled={busy}
                  className="w-full sm:w-auto"
                >
                  <Unlink className="mr-2 h-4 w-4" />
                  Unlink Folder
                </Button>
              )}
            </div>

            <Dialog
              open={adoptPreview !== null}
              onOpenChange={open => {
                if (!open) {
                  setAdoptPreview(null);
                  setPendingAdoptFolder(null);
                }
              }}
            >
              <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Use existing Drive folders?</DialogTitle>
                  <DialogDescription>
                    {adoptPreview?.root_folder_name
                      ? `Root folder: ${adoptPreview.root_folder_name}`
                      : 'Review how Richtato will link your existing account folders.'}
                  </DialogDescription>
                </DialogHeader>

                {adoptPreview && (
                  <div className="space-y-4 text-sm">
                    {adoptPreview.adopted.length > 0 && (
                      <section className="space-y-2">
                        <h3 className="font-medium text-foreground">
                          Will adopt ({adoptPreview.adopted.length})
                        </h3>
                        <ul className="space-y-1 text-muted-foreground">
                          {adoptPreview.adopted.map(item => (
                            <li key={item.folder_id}>
                              {item.account_name} → {item.folder_name}
                              {item.statement_file_count > 0
                                ? ` (${item.statement_file_count} statement file${item.statement_file_count === 1 ? '' : 's'})`
                                : ''}
                            </li>
                          ))}
                        </ul>
                      </section>
                    )}

                    {adoptPreview.would_create.length > 0 && (
                      <section className="space-y-2">
                        <h3 className="font-medium text-foreground">
                          Will create ({adoptPreview.would_create.length})
                        </h3>
                        <ul className="space-y-1 text-muted-foreground">
                          {adoptPreview.would_create.map(item => (
                            <li key={item.account_id}>
                              {item.account_name} → {item.expected_folder_name}
                            </li>
                          ))}
                        </ul>
                      </section>
                    )}

                    {adoptPreview.unmatched.length > 0 && (
                      <section className="space-y-2">
                        <h3 className="font-medium text-foreground">
                          Unmatched ({adoptPreview.unmatched.length})
                        </h3>
                        <ul className="space-y-1 text-muted-foreground">
                          {adoptPreview.unmatched.map(item => (
                            <li key={item.folder_id}>
                              {item.folder_name}
                              {item.parsed_account_id
                                ? ` (account ${item.parsed_account_id} not found)`
                                : ' (no account ID prefix)'}
                            </li>
                          ))}
                        </ul>
                      </section>
                    )}
                  </div>
                )}

                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setAdoptPreview(null);
                      setPendingAdoptFolder(null);
                    }}
                    disabled={busy}
                  >
                    Cancel
                  </Button>
                  <Button onClick={() => void confirmAdopt()} disabled={busy}>
                    {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Link Existing Folders
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

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
                    Accounts will stop syncing new statements to Drive. Files
                    already in Google Drive stay there. Your Google account
                    stays connected so you can choose a different folder later.
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
