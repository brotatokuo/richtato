const BALANCE_ON_DATE_ACCOUNT_TYPES = new Set([
  'checking',
  'savings',
  'investment',
]);

export function canSetBalanceOnDate(account: {
  account_type?: string;
  type?: string;
  sync_capabilities?: { balance_snapshots?: boolean };
}): boolean {
  const accountType = account.account_type || account.type || '';
  if (!BALANCE_ON_DATE_ACCOUNT_TYPES.has(accountType)) {
    return false;
  }
  return account.sync_capabilities?.balance_snapshots !== false;
}
