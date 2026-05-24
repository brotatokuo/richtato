import { statementFileService, type StatementFileRecord } from '@/lib/api/statementFiles';

export function getStatementFileUrl(file: StatementFileRecord): string {
  if (file.drive_file_url) {
    return file.drive_file_url;
  }
  return statementFileService.getDownloadUrl(file.id);
}

export function isDriveStatementFile(file: StatementFileRecord): boolean {
  return Boolean(file.drive_file_url || file.stored_path.startsWith('gdrive://'));
}
