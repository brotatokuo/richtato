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
      <CardContent className="p-4">
        <div className="flex gap-4 flex-wrap items-center min-w-0">
          <div className="flex-1 min-w-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search transactions..."
                value={searchTerm}
                onChange={e => onSearchChange(e.target.value)}
                className="pl-10 min-w-0"
              />
            </div>
          </div>
          <Button variant="outline" className="hidden md:inline-flex">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
