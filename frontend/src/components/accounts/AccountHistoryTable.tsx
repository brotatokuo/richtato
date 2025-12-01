import { AccountBalanceForm } from '@/components/accounts/AccountBalanceForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Modal } from '@/components/ui/Modal';
import { Pagination } from '@/components/ui/Pagination';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { usePreferences } from '@/contexts/PreferencesContext';
import { formatCurrency, formatDate } from '@/lib/format';
import { Account, transactionsApiService } from '@/lib/api/transactions';
import { ArrowUpDown, History, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';

interface AccountTransaction {
  id: number;
  date: string;
  amount: string;
}

interface AccountHistoryTableProps {
  accountId: number | null;
  accounts: Account[];
  onDataChange: () => void;
}

export function AccountHistoryTable({
  accountId,
  accounts,
  onDataChange,
}: AccountHistoryTableProps) {
  const { preferences } = usePreferences();
  const [transactions, setTransactions] = useState<AccountTransaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] =
    useState<AccountTransaction | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    loadTransactions();
  }, [accountId, accounts]);

  const loadTransactions = async () => {
    setLoading(true);
    try {
      if (accountId === null) {
        // Load all account transactions
        const promises = accounts.map(acc =>
          transactionsApiService.getAccountTransactions(acc.id, {
            page: 1,
            pageSize: 1000,
          })
        );
        const results = await Promise.all(promises);
        const allTransactions = results.flatMap((r, idx) =>
          (r.rows || []).map((tx: any) => ({
            id: tx.id,
            date: tx.date,
            amount: tx.amount,
            accountId: accounts[idx].id,
            accountName: accounts[idx].name,
          }))
        );
        setTransactions(allTransactions);
      } else {
        // Load single account transactions
        const data = await transactionsApiService.getAccountTransactions(
          accountId,
          { page: 1, pageSize: 1000 }
        );
        const account = accounts.find(a => a.id === accountId);
        const txWithAccount = (data.rows || []).map((tx: any) => ({
          id: tx.id,
          date: tx.date,
          amount: tx.amount,
          accountId: accountId,
          accountName: account?.name || '',
        }));
        setTransactions(txWithAccount);
      }
    } catch (error) {
      console.error('Error loading account transactions:', error);
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const sortedTransactions = [...transactions].sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return sortDirection === 'asc' ? dateA - dateB : dateB - dateA;
  });

  // Pagination calculations
  const totalItems = sortedTransactions.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedTransactions = sortedTransactions.slice(startIndex, endIndex);

  const handleSort = () => {
    setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
  };

  const handleAddSubmit = async (data: {
    balance: number;
    date: string;
  }) => {
    if (accountId === null) {
      alert('Please select an account first');
      return;
    }

    try {
      await transactionsApiService.createAccountTransaction({
        account: accountId,
        amount: data.balance,
        date: data.date,
      });
      await loadTransactions();
      setShowAddModal(false);
      onDataChange();
    } catch (error) {
      console.error('Error adding balance:', error);
      throw error;
    }
  };

  const handleEditSubmit = async (data: {
    balance: number;
    date: string;
    id?: number;
  }) => {
    if (!selectedTransaction || !data.id) return;
    const txAccount = (selectedTransaction as any).accountId;

    try {
      await transactionsApiService.updateAccountTransaction(txAccount, {
        id: data.id,
        amount: data.balance,
        date: data.date,
      });
      await loadTransactions();
      setShowEditModal(false);
      setSelectedTransaction(null);
      onDataChange();
    } catch (error) {
      console.error('Error updating balance:', error);
      throw error;
    }
  };

  const handleDelete = async () => {
    if (!selectedTransaction) return;
    const confirmDelete = window.confirm(
      'Delete this balance record?'
    );
    if (!confirmDelete) return;

    const txAccount = (selectedTransaction as any).accountId;

    try {
      await transactionsApiService.deleteAccountTransaction(
        txAccount,
        selectedTransaction.id
      );
      await loadTransactions();
      setShowEditModal(false);
      setSelectedTransaction(null);
      onDataChange();
    } catch (error) {
      console.error('Error deleting balance:', error);
    }
  };

  const openEditModal = (tx: AccountTransaction) => {
    setSelectedTransaction(tx);
    setShowEditModal(true);
  };

  const selectedAccount = accountId
    ? accounts.find(a => a.id === accountId)
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-card-foreground flex items-center gap-2">
            <History className="h-6 w-6 text-primary" />
            {accountId === null ? 'All Account History' : 'Account History'}
          </h2>
          {selectedAccount && (
            <p className="text-sm text-muted-foreground mt-1">
              {selectedAccount.name}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setShowAddModal(true)}
            variant="default"
            disabled={accountId === null}
            title={
              accountId === null
                ? 'Select an account to add balance'
                : 'Add balance update'
            }
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Balance Update
          </Button>
        </div>
      </div>

      {/* Add Modal */}
      {selectedAccount && (
        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title={`Add Balance Update - ${selectedAccount.name}`}
        >
          <AccountBalanceForm
            accountId={selectedAccount.id}
            accountName={selectedAccount.name}
            onSubmit={handleAddSubmit}
            onCancel={() => setShowAddModal(false)}
          />
        </Modal>
      )}

      {/* Mobile list (<= md) */}
      <div className="md:hidden">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="p-0">
            {loading ? (
              <div className="py-8 text-center text-sm">
                Loading transactions...
              </div>
            ) : (
              <div className="divide-y">
                {paginatedTransactions.map((tx, index) => {
                  const amount = parseFloat(tx.amount);
                  const accountName = (tx as any).accountName || '';
                  return (
                    <div
                      key={`${tx.id}-${index}`}
                      className="p-4 w-full flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between cursor-pointer hover:bg-muted/30"
                      onClick={() => openEditModal(tx)}
                    >
                      <div className="space-y-1 min-w-0 sm:pr-2">
                        <div className="text-sm font-medium">
                          {formatDate(tx.date, preferences.date_format)}
                        </div>
                        {accountId === null && (
                          <div className="text-xs text-muted-foreground">
                            {accountName}
                          </div>
                        )}
                      </div>
                      <div
                        className={`sm:ml-4 sm:text-right text-sm font-semibold ${
                          amount >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {formatCurrency(amount, preferences.currency)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Table (md+) */}
      <div className="hidden md:block overflow-x-auto">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50 min-w-0">
          <CardContent className="p-0 min-w-0">
            <div className="min-w-full">
              <Table className="min-w-full table-fixed md:table-auto">
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={handleSort}
                    >
                      <div className="flex items-center gap-2">
                        Date
                        <ArrowUpDown className="h-4 w-4" />
                      </div>
                    </TableHead>
                    {accountId === null && (
                      <TableHead>Account</TableHead>
                    )}
                    <TableHead className="text-right">Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell
                        colSpan={accountId === null ? 3 : 2}
                        className="text-center py-8"
                      >
                        <div className="flex items-center justify-center gap-2">
                          Loading transactions...
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedTransactions.map((tx, index) => {
                      const amount = parseFloat(tx.amount);
                      const accountName = (tx as any).accountName || '';
                      return (
                        <TableRow
                          key={`${tx.id}-${index}`}
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => openEditModal(tx)}
                          title="Click to edit"
                        >
                          <TableCell className="font-medium">
                            {formatDate(tx.date, preferences.date_format)}
                          </TableCell>
                          {accountId === null && (
                            <TableCell>{accountName}</TableCell>
                          )}
                          <TableCell
                            className={`text-right font-medium ${
                              amount >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {formatCurrency(amount, preferences.currency)}
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        totalItems={totalItems}
        itemsPerPage={itemsPerPage}
      />

      {totalItems === 0 && !loading && (
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">
              {accountId === null
                ? 'No transaction history found.'
                : 'No balance history for this account. Add a balance update to get started.'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Edit Modal */}
      {selectedTransaction && (
        <Modal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setSelectedTransaction(null);
          }}
          title="Edit Balance Update"
        >
          <AccountBalanceForm
            accountId={(selectedTransaction as any).accountId}
            accountName={(selectedTransaction as any).accountName || ''}
            initialData={{
              balance: selectedTransaction.amount,
              date: selectedTransaction.date,
              id: selectedTransaction.id,
            }}
            onSubmit={handleEditSubmit}
            onDelete={handleDelete}
            onCancel={() => {
              setShowEditModal(false);
              setSelectedTransaction(null);
            }}
          />
        </Modal>
      )}
    </div>
  );
}
