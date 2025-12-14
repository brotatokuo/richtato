import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { CategoryKeyword, categorySettingsApi } from '@/lib/api/user';
import { Search, Trash2, X } from 'lucide-react';
import { FormEvent, useEffect, useState } from 'react';

interface BulkKeywordsModalProps {
  open: boolean;
  onClose: () => void;
  categoryId: number;
  categoryName: string;
  categoryIcon: string;
  onKeywordsChanged?: () => void;
}

export function BulkKeywordsModal({
  open,
  onClose,
  categoryId,
  categoryName,
  categoryIcon,
  onKeywordsChanged,
}: BulkKeywordsModalProps) {
  const [keywords, setKeywords] = useState<CategoryKeyword[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newKeyword, setNewKeyword] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [adding, setAdding] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Load keywords when modal opens
  useEffect(() => {
    if (open && categoryId) {
      loadKeywords();
    }
  }, [open, categoryId]);

  const loadKeywords = async () => {
    try {
      setLoading(true);
      setError(null);
      const response =
        await categorySettingsApi.getCategoryKeywords(categoryId);
      setKeywords(response.keywords);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load keywords');
    } finally {
      setLoading(false);
    }
  };

  const handleAddKeyword = async (e?: FormEvent) => {
    e?.preventDefault();
    const keyword = newKeyword.trim();
    if (!keyword) return;

    try {
      setAdding(true);
      setError(null);
      const newKeywordObj = await categorySettingsApi.addCategoryKeyword(
        categoryId,
        keyword
      );
      setKeywords(prev => [...prev, newKeywordObj]);
      setNewKeyword('');
      onKeywordsChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add keyword');
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteKeyword = async (keywordId: number) => {
    try {
      setDeletingId(keywordId);
      setError(null);
      await categorySettingsApi.deleteCategoryKeyword(categoryId, keywordId);
      setKeywords(prev => prev.filter(k => k.id !== keywordId));
      onKeywordsChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete keyword');
    } finally {
      setDeletingId(null);
    }
  };

  // Filter keywords based on search
  const filteredKeywords = keywords.filter(kw =>
    kw.keyword.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Sort by match count (descending), then alphabetically
  const sortedKeywords = [...filteredKeywords].sort((a, b) => {
    if (b.match_count !== a.match_count) {
      return b.match_count - a.match_count;
    }
    return a.keyword.localeCompare(b.keyword);
  });

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="text-2xl">{categoryIcon}</span>
            Edit Keywords: {categoryName}
          </DialogTitle>
          <DialogDescription>
            Manage keywords that automatically categorize transactions. Keywords
            are matched case-insensitively against transaction descriptions.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col gap-4">
          {/* Add new keyword */}
          <form onSubmit={handleAddKeyword} className="flex gap-2">
            <Input
              placeholder="Add new keyword (e.g., walmart, netflix)"
              value={newKeyword}
              onChange={e => setNewKeyword(e.target.value)}
              disabled={adding}
              className="flex-1"
            />
            <Button type="submit" disabled={!newKeyword.trim() || adding}>
              {adding ? 'Adding...' : 'Add'}
            </Button>
          </form>

          {/* Search keywords */}
          {keywords.length > 0 && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search keywords..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="text-sm text-red-600 bg-red-50 dark:bg-red-950/30 p-2 rounded">
              {error}
            </div>
          )}

          {/* Keywords list */}
          <div className="flex-1 overflow-y-auto border rounded-lg">
            {loading ? (
              <div className="p-8 text-center text-sm text-muted-foreground">
                Loading keywords...
              </div>
            ) : sortedKeywords.length === 0 ? (
              <div className="p-8 text-center text-sm text-muted-foreground">
                {searchQuery
                  ? 'No keywords match your search'
                  : 'No keywords yet. Add one above to get started.'}
              </div>
            ) : (
              <div className="divide-y">
                {sortedKeywords.map(kw => (
                  <div
                    key={kw.id}
                    className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-sm truncate">
                        {kw.keyword}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-sm text-muted-foreground whitespace-nowrap">
                        {kw.match_count}{' '}
                        {kw.match_count === 1 ? 'match' : 'matches'}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteKeyword(kw.id)}
                        disabled={deletingId === kw.id}
                        className="h-8 w-8 p-0"
                      >
                        {deletingId === kw.id ? (
                          <X className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4 text-red-500" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Summary */}
          {keywords.length > 0 && (
            <div className="text-sm text-muted-foreground text-center pb-2">
              {keywords.length} {keywords.length === 1 ? 'keyword' : 'keywords'}{' '}
              total
              {searchQuery && filteredKeywords.length !== keywords.length && (
                <span> · {filteredKeywords.length} shown</span>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
