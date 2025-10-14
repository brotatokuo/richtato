import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Account, Category } from '@/lib/api/transactions';
import { TransactionFormData, TransactionType } from '@/types/transactions';

interface TransactionFormProps {
  type: TransactionType;
  formData: TransactionFormData;
  onFormChange: (data: TransactionFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  accounts: Account[];
  categories: Category[];
}

export function TransactionForm({
  type,
  formData,
  onFormChange,
  onSubmit,
  onCancel,
  accounts,
  categories,
}: TransactionFormProps) {
  const isIncome = type === 'income';
  const colorClass = isIncome ? 'green' : 'red';
  const title = isIncome ? 'Income' : 'Expense';
  const placeholder = isIncome
    ? 'e.g., Salary, Freelance work'
    : 'e.g., Groceries, Gas, Coffee';

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor={`${type}-description`}>Description</Label>
          <Input
            id={`${type}-description`}
            value={formData.description}
            onChange={e =>
              onFormChange({
                ...formData,
                description: e.target.value,
              })
            }
            placeholder={placeholder}
            required
          />
        </div>
        <div>
          <Label htmlFor={`${type}-amount`}>Amount</Label>
          <Input
            id={`${type}-amount`}
            type="number"
            step="0.01"
            min="0"
            value={formData.amount}
            onChange={e =>
              onFormChange({
                ...formData,
                amount: e.target.value,
              })
            }
            placeholder="0.00"
            required
          />
        </div>
        <div>
          <Label htmlFor={`${type}-date`}>Date</Label>
          <Input
            id={`${type}-date`}
            type="date"
            value={formData.date}
            onChange={e =>
              onFormChange({
                ...formData,
                date: e.target.value,
              })
            }
            required
          />
        </div>
        <div>
          <Label htmlFor={`${type}-account`}>Account</Label>
          <Select
            value={formData.account_name}
            onValueChange={value =>
              onFormChange({
                ...formData,
                account_name: value,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select account" />
            </SelectTrigger>
            <SelectContent>
              {accounts.map(account => (
                <SelectItem key={account.id} value={account.name}>
                  {account.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {!isIncome && (
          <div className="md:col-span-2">
            <Label htmlFor={`${type}-category`}>Category</Label>
            <Select
              value={formData.category || ''}
              onValueChange={value =>
                onFormChange({
                  ...formData,
                  category: value,
                })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map(category => (
                  <SelectItem key={category.id} value={category.name}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <Button
          type="submit"
          className={`bg-${colorClass}-600 hover:bg-${colorClass}-700`}
        >
          Add {title}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
