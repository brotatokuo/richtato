import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';
import React from 'react';

interface FileSearchBarProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  fileCount: number;
}

export const FileSearchBar: React.FC<FileSearchBarProps> = ({
  searchValue,
  onSearchChange,
  fileCount,
}) => {
  return (
    <div className="flex items-center gap-4">
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search files..."
          value={searchValue}
          onChange={e => onSearchChange(e.target.value)}
          className="pl-10"
        />
      </div>
      <div className="text-sm text-muted-foreground">
        {fileCount} file{fileCount !== 1 ? 's' : ''}
      </div>
    </div>
  );
};
