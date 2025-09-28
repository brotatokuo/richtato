import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { TransactionType } from '@/types/transactions';
import { Download, Search } from 'lucide-react';

interface SearchAndFilterProps {
  type: TransactionType;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  filterCategory: string;
  onFilterChange: (category: string) => void;
  categories: string[];
}

export function SearchAndFilter({
  type,
  searchTerm,
  onSearchChange,
  filterCategory,
  onFilterChange,
  categories,
}: SearchAndFilterProps) {
  const isIncome = type === 'income';
  const placeholder = isIncome
    ? 'Search income transactions...'
    : 'Search expense transactions...';

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardContent className="p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={placeholder}
                value={searchTerm}
                onChange={e => onSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          {!isIncome && (
            <div className="w-48">
              <Select
                value={filterCategory || 'all'}
                onValueChange={value =>
                  onFilterChange(value === 'all' ? '' : value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
