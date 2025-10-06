# File Management Components

A modular file management system with responsive column configuration and customizable layouts.

## Components

### Core Components

- **FileTable**: Main table component with configurable columns
- **FileUploadArea**: Drag and drop file upload interface
- **FileSearchBar**: Search and filter controls
- **FileEditModal**: Modal for editing file metadata

### Hooks

- **useResponsiveColumns**: Hook for managing responsive column visibility

## Usage

### Basic Usage

```tsx
import {
  FileTable,
  FileUploadArea,
  FileSearchBar,
  FileEditModal,
  useResponsiveColumns,
  defaultFileTableConfig,
} from '@/components/file-management';

function MyFileManager() {
  const { config, showAllColumns, setShowAllColumns } = useResponsiveColumns(
    defaultFileTableConfig
  );

  return (
    <div>
      <FileUploadArea {...uploadProps} />
      <FileSearchBar {...searchProps} />
      <FileTable files={files} config={config} {...tableProps} />
      <FileEditModal {...modalProps} />
    </div>
  );
}
```

### Custom Column Configuration

```tsx
import {
  createCustomConfig,
  defaultFileTableConfig,
} from '@/components/file-management';

// Create a custom configuration
const customConfig = createCustomConfig(
  defaultFileTableConfig,
  ['name', 'type', 'size', 'status', 'actions'], // Visible columns
  ['name', 'status', 'type', 'size', 'actions'] // Column order
);

// Use with FileTable
<FileTable files={files} config={customConfig} {...props} />;
```

### Responsive Design

The system automatically adjusts columns based on screen size:

- **Mobile** (< 768px): Shows only high-priority columns
- **Tablet** (768px - 1024px): Shows medium and high-priority columns
- **Desktop** (> 1024px): Shows all columns

### Column Configuration

Each column can be configured with:

```tsx
{
  id: 'name',
  label: 'Name',
  size: 250,
  minSize: 200,
  priority: 'high' | 'medium' | 'low',
  responsive: {
    mobile: true,
    tablet: true,
    desktop: true,
  },
  order: 1,
}
```

### Available Columns

- `name`: File name with icon
- `type`: File type badge
- `size`: File size
- `status`: Processing status
- `uploader`: Uploader name
- `tags`: File tags
- `equipment`: Associated equipment
- `accessGroup`: Access group
- `uploadDate`: Upload date
- `actions`: Action buttons (download, edit, delete)

### Examples

See `examples.ts` for pre-configured layouts:

- `mobileFirstConfig`: Minimal columns for mobile
- `detailedConfig`: All columns for detailed view
- `adminConfig`: Admin-focused columns
- `equipmentConfig`: Equipment-focused view

## Customization

### Adding New Columns

1. Add column ID to `ColumnId` type
2. Add column configuration to config
3. Add cell component to `columnDefinitions.tsx`
4. Add column mapping in `createColumnDefinitions`

### Custom Cell Components

Create custom cell components in `columnDefinitions.tsx`:

```tsx
const CustomCell = ({ value }: { value: string }) => (
  <div className="custom-cell">{value}</div>
);
```

### Custom Configurations

Create custom configurations for specific use cases:

```tsx
const myConfig: FileTableConfig = {
  columns: [
    // Your column definitions
  ],
  defaultView: 'compact',
  responsiveBreakpoints: {
    mobile: 640,
    tablet: 768,
    desktop: 1024,
  },
};
```
