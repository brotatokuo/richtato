# Simulation Chat System

A modular simulation system for the Synapse AI chat interface that allows for realistic, timed conversations simulating datacenter operations and emergency scenarios.

## Overview

The simulation chat system enables the creation of interactive, scripted conversations that simulate real-world datacenter scenarios. Users can trigger simulations through notifications or manual selection, and the system will play out a realistic conversation with proper timing, internal processing indicators, and progress tracking.

## Architecture

### Core Components

1. **SimulationConfigs** (`/data/simulationConfigs.ts`) - Configuration definitions for different simulation scenarios
2. **SimulationService** (`/services/simulationService.ts`) - Core simulation engine that manages timing and message delivery
3. **ChatSidebar** (`/components/ChatSidebar.tsx`) - Enhanced chat interface with simulation controls
4. **SimulationNotification** (`/components/SimulationNotification.tsx`) - Notification component for triggering simulations

### Key Features

- **Modular Configuration**: JSON-based simulation definitions that can be easily extended
- **Realistic Timing**: Configurable delays between messages and internal processing indicators
- **Progress Tracking**: Visual progress indicators and step-by-step execution
- **Interactive Controls**: Start, stop, and progress monitoring for simulations
- **Notification Integration**: Trigger simulations through notification components
- **Type Safety**: Full TypeScript support with proper type definitions

## Usage

### Basic Implementation

```tsx
import { ChatSidebar } from "@/components/ChatSidebar";

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [simulationId, setSimulationId] = useState<string>();

  return (
    <div>
      {/* Trigger simulation via notification */}
      <SimulationNotification
        simulationId="power-anomaly-hvac"
        title="Power Anomaly Detected"
        message="SC1-HVAC1A power consumption dropped to 47W"
        severity="critical"
        onTrigger={setSimulationId}
      />

      {/* Chat sidebar with simulation support */}
      <ChatSidebar
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        simulationId={simulationId}
      />
    </div>
  );
}
```

### Creating Custom Simulations

1. **Define Simulation Configuration**:

```typescript
// In simulationConfigs.ts
export const customSimulation: SimulationConfig = {
  id: "custom-scenario",
  name: "Custom Scenario",
  description: "A custom simulation scenario",
  triggerType: "notification",
  autoStart: false,
  messages: [
    {
      id: "1",
      content: "Initial message content",
      sender: "bot",
      timestamp: new Date(),
      delay: 0, // Immediate
    },
    {
      id: "2",
      content: "Follow-up message",
      sender: "bot",
      timestamp: new Date(),
      delay: 2000, // 2 seconds delay
      internal: "Processing system diagnostics...", // Internal processing text
      internalDelay: 5000, // 5 seconds of internal processing
    },
    // ... more messages
  ],
};
```

2. **Add to Available Simulations**:

```typescript
// Add to simulationConfigs array
export const simulationConfigs: SimulationConfig[] = [
  // ... existing simulations
  customSimulation,
];
```

### Advanced Features

#### Internal Processing Indicators

Simulations can show internal processing messages to simulate AI thinking:

```typescript
{
  id: '3',
  content: 'Analysis complete',
  sender: 'bot',
  timestamp: new Date(),
  delay: 1000,
  internal: 'Analyzing power consumption patterns...',
  internalDelay: 3000, // Shows for 3 seconds
}
```

#### File Attachments

Simulations can include file attachments:

```typescript
{
  id: '4',
  content: 'I found the relevant documentation',
  sender: 'bot',
  timestamp: new Date(),
  attachedFiles: [
    {
      id: 'doc-1',
      name: 'HVAC-DiagnosticProcedures_v4.1.pdf',
      size: 2048000,
      type: 'application/pdf',
    },
  ],
}
```

#### Conditional Messaging

Use delays and internal processing to create realistic conversation flow:

```typescript
// Immediate response
{ delay: 0, content: 'Alert received...' }

// Quick follow-up
{ delay: 1000, content: 'Investigating...' }

// Longer analysis with internal processing
{
  delay: 2000,
  content: 'Analysis complete',
  internal: 'Cross-referencing with historical data...',
  internalDelay: 10000
}
```

## API Reference

### SimulationConfig Interface

```typescript
interface SimulationConfig {
  id: string; // Unique identifier
  name: string; // Display name
  description: string; // Description for UI
  triggerType: "notification" | "manual" | "auto";
  messages: SimulationMessage[]; // Array of messages
  autoStart?: boolean; // Auto-start when opened
  duration?: number; // Total duration in ms
}
```

### SimulationMessage Interface

```typescript
interface SimulationMessage {
  id: string; // Unique message ID
  content: string; // Message content
  sender: "user" | "bot"; // Message sender
  timestamp: Date; // Message timestamp
  delay?: number; // Delay before showing (ms)
  internal?: string; // Internal processing text
  internalDelay?: number; // Internal processing duration (ms)
  attachedFiles?: AttachedFile[]; // Optional file attachments
}
```

### SimulationService Methods

```typescript
class SimulationService {
  start(): void; // Start the simulation
  stop(): void; // Stop the simulation
  destroy(): void; // Clean up resources
  getState(): SimulationState; // Get current state
  getProgress(): number; // Get progress percentage (0-100)
}
```

## Built-in Simulations

### 1. Power Anomaly - HVAC Failure

- **ID**: `power-anomaly-hvac`
- **Description**: Simulates an HVAC power anomaly scenario with system diagnostics
- **Duration**: ~3 minutes
- **Features**: Multi-step troubleshooting, internal processing, file references

### 2. Temperature Spike Alert

- **ID**: `temperature-spike`
- **Description**: Simulates a temperature spike scenario in the datacenter
- **Duration**: ~30 seconds
- **Features**: Quick diagnosis and resolution

### 3. Power Outage Simulation

- **ID**: `power-outage`
- **Description**: Simulates a power outage scenario with backup systems
- **Duration**: ~45 seconds
- **Features**: Critical alert handling, backup system activation

## Integration Examples

### With Notification System

```tsx
// Dashboard component
function Dashboard() {
  const [activeSimulation, setActiveSimulation] = useState<string>();

  return (
    <div>
      {/* Show notifications */}
      <SimulationNotification
        simulationId="power-anomaly-hvac"
        title="Critical Alert"
        message="HVAC system failure detected"
        severity="critical"
        onTrigger={(id) => {
          setActiveSimulation(id);
          setChatOpen(true);
        }}
      />

      {/* Chat with simulation */}
      <ChatSidebar
        isOpen={isChatOpen}
        simulationId={activeSimulation}
        onClose={() => setChatOpen(false)}
      />
    </div>
  );
}
```

### With Manual Controls

```tsx
// Manual simulation selection
function SimulationControls() {
  const [selectedSim, setSelectedSim] = useState<string>();

  return (
    <div>
      <select onChange={(e) => setSelectedSim(e.target.value)}>
        <option value="">Select Simulation</option>
        {simulationConfigs.map((sim) => (
          <option key={sim.id} value={sim.id}>
            {sim.name}
          </option>
        ))}
      </select>

      <ChatSidebar
        simulationId={selectedSim}
        // ... other props
      />
    </div>
  );
}
```

## Styling and Customization

### CSS Classes

The simulation system uses Tailwind CSS classes that can be customized:

- `.simulation-progress` - Progress bar styling
- `.simulation-controls` - Control button styling
- `.internal-processing` - Internal processing indicator styling

### Theme Integration

The system respects the application's theme context and will automatically adapt to light/dark modes.

## Performance Considerations

- **Memory Management**: Simulations automatically clean up timeouts and resources
- **Concurrent Simulations**: Only one simulation can run at a time
- **Large Simulations**: For simulations with many messages, consider pagination or lazy loading
- **Timeout Management**: All timeouts are properly cleared on component unmount

## Troubleshooting

### Common Issues

1. **Simulation not starting**: Check that the simulation ID exists in the configs
2. **Messages not appearing**: Verify the delay values and internal processing settings
3. **Memory leaks**: Ensure proper cleanup by calling `destroy()` on unmount
4. **Type errors**: Make sure all message properties match the interface definitions

### Debug Mode

Enable debug logging by setting the environment variable:

```bash
REACT_APP_DEBUG_SIMULATIONS=true
```

This will log simulation state changes and timing information to the console.

## Contributing

When adding new simulations:

1. Follow the existing naming conventions
2. Include proper TypeScript types
3. Add realistic timing and delays
4. Test with different screen sizes and themes
5. Update this documentation

## Future Enhancements

- **Voice Integration**: Add text-to-speech for simulation messages
- **Interactive Elements**: Allow user responses during simulations
- **Simulation Analytics**: Track simulation usage and completion rates
- **Dynamic Content**: Support for dynamic content based on system state
- **Multi-language Support**: Internationalization for simulation content
