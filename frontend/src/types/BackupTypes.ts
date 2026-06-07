export interface Backup {
  name: string;
  created_at: string;
  size_bytes: number;
}

export interface BackupList {
  backups: Backup[];
  total: number;
}
