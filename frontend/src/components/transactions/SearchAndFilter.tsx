import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Download, Search } from 'lucide-react';

interface SearchAndFilterProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
}

export function SearchAndFilter({
  searchTerm,
  onSearchChange,
}: SearchAndFilterProps) {
  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50">
      <CardContent className="p-2">
        <div className="flex gap-2 flex-wrap items-center min-w-0">
          <div className="flex-1 min-w-0">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search transactions..."
                value={searchTerm}
                onChange={e => onSearchChange(e.target.value)}
                className="pl-8 h-8 text-sm min-w-0"
              />
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="hidden md:inline-flex h-8"
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
