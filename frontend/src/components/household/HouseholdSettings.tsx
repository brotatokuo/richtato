import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useHousehold } from '@/contexts/HouseholdContext';
import { householdApi } from '@/lib/api/household';
import { Copy, LogOut, UserPlus, Users } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

export function HouseholdSettings() {
  const { household, isInHousehold, members, refreshHousehold } =
    useHousehold();
  const [createName, setCreateName] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreate = async () => {
    if (!createName.trim()) return;
    setIsSubmitting(true);
    try {
      await householdApi.createHousehold(createName.trim());
      await refreshHousehold();
      setCreateName('');
      toast.success('Household created');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleJoin = async () => {
    if (!joinCode.trim()) return;
    setIsSubmitting(true);
    try {
      await householdApi.joinHousehold(joinCode.trim());
      await refreshHousehold();
      setJoinCode('');
      toast.success('Joined household');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Invalid code');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGenerateInvite = async () => {
    try {
      const result = await householdApi.generateInviteCode();
      setInviteCode(result.invite_code);
      toast.success('Invite code generated');
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to generate code'
      );
    }
  };

  const handleCopyCode = () => {
    if (inviteCode) {
      navigator.clipboard.writeText(inviteCode);
      toast.success('Code copied to clipboard');
    }
  };

  const handleLeave = async () => {
    if (!confirm('Are you sure you want to leave this household?')) return;
    setIsSubmitting(true);
    try {
      await householdApi.leaveHousehold();
      await refreshHousehold();
      setInviteCode(null);
      toast.success('Left household');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to leave');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isInHousehold && household) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            {household.name}
          </CardTitle>
          <CardDescription>
            Manage your household and share finances with your partner.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="text-sm font-medium mb-2">Members</h4>
            <div className="space-y-2">
              {members.map(m => (
                <div
                  key={m.user_id}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <span className="text-sm">{m.username}</span>
                  <span className="text-xs text-muted-foreground">
                    Joined {new Date(m.joined_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {members.length < 2 && (
            <div>
              <h4 className="text-sm font-medium mb-2">Invite Partner</h4>
              {inviteCode ? (
                <div className="flex items-center gap-2">
                  <code className="flex-1 rounded-md border bg-muted px-3 py-2 text-sm font-mono">
                    {inviteCode}
                  </code>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={handleCopyCode}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  onClick={handleGenerateInvite}
                  className="gap-2"
                >
                  <UserPlus className="h-4 w-4" />
                  Generate Invite Code
                </Button>
              )}
            </div>
          )}

          <Button
            variant="destructive"
            size="sm"
            onClick={handleLeave}
            disabled={isSubmitting}
            className="gap-2"
          >
            <LogOut className="h-4 w-4" />
            Leave Household
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Household
        </CardTitle>
        <CardDescription>
          Create a household or join an existing one to share finances with your
          partner.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Create a Household</h4>
          <div className="flex gap-2">
            <Input
              placeholder="Household name"
              value={createName}
              onChange={e => setCreateName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
            />
            <Button
              onClick={handleCreate}
              disabled={isSubmitting || !createName.trim()}
            >
              Create
            </Button>
          </div>
        </div>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-card px-2 text-muted-foreground">or</span>
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium">Join a Household</h4>
          <div className="flex gap-2">
            <Input
              placeholder="Enter invite code"
              value={joinCode}
              onChange={e => setJoinCode(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleJoin()}
            />
            <Button
              variant="outline"
              onClick={handleJoin}
              disabled={isSubmitting || !joinCode.trim()}
            >
              Join
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
