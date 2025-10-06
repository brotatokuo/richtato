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
import { Label } from '@/components/ui/label';
import React, { useState } from 'react';
import { FileItem } from './types';

interface FileEditModalProps {
  file: FileItem | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (file: FileItem) => void;
}

export const FileEditModal: React.FC<FileEditModalProps> = ({
  file,
  isOpen,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState({
    tags: file?.tags.join(', ') || '',
    accessGroup: file?.accessGroup || '',
    equipment: file?.equipment || '',
    status: file?.status || 'uploaded',
    description: file?.description || '',
  });

  React.useEffect(() => {
    if (file) {
      setFormData({
        tags: file.tags.join(', '),
        accessGroup: file.accessGroup,
        equipment: file.equipment,
        status: file.status,
        description: file.description || '',
      });
    }
  }, [file]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    const updatedFile = {
      ...file,
      tags: formData.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag),
      accessGroup: formData.accessGroup,
      equipment: formData.equipment,
      status: formData.status as FileItem['status'],
      description: formData.description,
    };
    onSave(updatedFile);
  };

  if (!file) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit File Metadata</DialogTitle>
          <DialogDescription>
            Update the metadata for {file.name}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <Input
              id="tags"
              value={formData.tags}
              onChange={e =>
                setFormData(prev => ({ ...prev, tags: e.target.value }))
              }
              placeholder="Enter tags separated by commas"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="accessGroup">Access Group</Label>
            <Input
              id="accessGroup"
              value={formData.accessGroup}
              onChange={e =>
                setFormData(prev => ({ ...prev, accessGroup: e.target.value }))
              }
              placeholder="Enter access group"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="equipment">Equipment</Label>
            <Input
              id="equipment"
              value={formData.equipment}
              onChange={e =>
                setFormData(prev => ({ ...prev, equipment: e.target.value }))
              }
              placeholder="Enter equipment name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <select
              id="status"
              value={formData.status}
              onChange={e =>
                setFormData(prev => ({
                  ...prev,
                  status: e.target.value as FileItem['status'],
                }))
              }
              className="w-full px-3 py-2 border border-input bg-background rounded-md"
            >
              <option value="uploaded">Uploaded</option>
              <option value="processing">Processing</option>
              <option value="vectorized">Vectorized</option>
              <option value="error">Error</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={formData.description}
              onChange={e =>
                setFormData(prev => ({ ...prev, description: e.target.value }))
              }
              placeholder="Enter file description"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Save Changes</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
