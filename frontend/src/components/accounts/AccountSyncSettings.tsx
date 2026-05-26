import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AGENT_CADENCE_OPTIONS,
  AGENT_HOUR_OPTIONS,
  SYNC_MODE_OPTIONS,
  agentFlowLabel,
  type AgentCadence,
  type AgentFlow,
  type SyncMode,
} from '@/lib/api/bankSync';
import { AlertTriangle, Bot } from 'lucide-react';
import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { InstitutionFieldChoice } from './AccountFormFields';

export interface AccountSyncFormValues {
  entity: string;
  type: string;
  syncMode: SyncMode;
  agentCadence: AgentCadence;
  agentSyncHour: number;
  agentActivityUrl: string;
}

interface AccountSyncSettingsProps {
  form: AccountSyncFormValues;
  institutions: InstitutionFieldChoice[];
  hasStorageUri?: boolean;
  onChange: (
    field: keyof Pick<
      AccountSyncFormValues,
      'syncMode' | 'agentCadence' | 'agentSyncHour' | 'agentActivityUrl'
    >,
    value: string | number
  ) => void;
  idPrefix?: string;
  disabled?: boolean;
}

function getAgentFlow(
  institutions: InstitutionFieldChoice[],
  entity: string,
  accountType: string
): AgentFlow | null {
  const institution = institutions.find(item => item.value === entity);
  const flow = institution?.agent_flows?.find(
    item => item.account_type === accountType
  )?.flow;
  return flow ?? null;
}

export function AccountSyncSettings({
  form,
  institutions,
  hasStorageUri = true,
  onChange,
  idPrefix = 'sync',
  disabled = false,
}: AccountSyncSettingsProps) {
  const agentFlow = getAgentFlow(institutions, form.entity, form.type);
  const autoSupported = Boolean(agentFlow);
  const needsStorage = agentFlow === 'deposit' || agentFlow === 'credit_card';
  const isAuto = form.syncMode === 'auto';

  useEffect(() => {
    if (isAuto && !autoSupported) {
      onChange('syncMode', 'manual');
    }
  }, [autoSupported, isAuto, onChange]);

  return (
    <div className="space-y-3 rounded-lg border border-border bg-muted/20 p-3">
      <div>
        <Label htmlFor={`${idPrefix}-mode`}>Import Method</Label>
        <Select
          value={form.syncMode}
          disabled={disabled}
          onValueChange={value => onChange('syncMode', value)}
        >
          <SelectTrigger id={`${idPrefix}-mode`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SYNC_MODE_OPTIONS.map(option => (
              <SelectItem
                key={option.value}
                value={option.value}
                disabled={option.value === 'auto' && !autoSupported}
              >
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!autoSupported && (
        <p className="rounded-md border border-border bg-background px-3 py-2 text-xs text-muted-foreground">
          Automatic import is not available for this bank and account type yet.
        </p>
      )}

      {isAuto && autoSupported && (
        <div className="space-y-3 border-t border-border pt-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Bot className="h-3.5 w-3.5" />
            <span>{agentFlowLabel(agentFlow)}</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label htmlFor={`${idPrefix}-cadence`}>Cadence</Label>
              <Select
                value={form.agentCadence}
                disabled={disabled}
                onValueChange={value => onChange('agentCadence', value)}
              >
                <SelectTrigger id={`${idPrefix}-cadence`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AGENT_CADENCE_OPTIONS.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor={`${idPrefix}-hour`}>Hour</Label>
              <Select
                value={String(form.agentSyncHour)}
                disabled={disabled}
                onValueChange={value =>
                  onChange('agentSyncHour', Number(value))
                }
              >
                <SelectTrigger id={`${idPrefix}-hour`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AGENT_HOUR_OPTIONS.map(option => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor={`${idPrefix}-activity-url`}>Activity URL</Label>
            <Input
              id={`${idPrefix}-activity-url`}
              type="url"
              value={form.agentActivityUrl}
              disabled={disabled}
              onChange={event =>
                onChange('agentActivityUrl', event.currentTarget.value)
              }
              placeholder="https://..."
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Paste the signed-in bank activity page the local Bank Agent should
              use for this account.
            </p>
          </div>

          {needsStorage && !hasStorageUri && (
            <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>
                Automatic statement import needs a Google Drive statement
                folder. Finish this account, then activate Drive in{' '}
                <Link
                  to="/setup?tab=statements"
                  className="font-medium underline underline-offset-2"
                >
                  Setup &gt; Statements
                </Link>
                .
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
