import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'
import { RefreshCw, Trash2, CheckCircle, XCircle } from 'lucide-react'
import { format } from 'date-fns'
import { cn } from '@/utils/cn'

const platformIcons = {
  leetcode: '🔥',
  codeforces: '⚔️',
  codechef: '👨‍🍳',
  github: '🐙',
  geeksforgeeks: '💚',
}

export function PlatformCard({ platform, onSync, onDisconnect, isLoading }) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{platformIcons[platform.platform_name] || '📊'}</span>
            <div>
              <CardTitle className="text-lg capitalize">{platform.platform_name}</CardTitle>
              <p className="text-sm text-muted-foreground">@{platform.platform_username}</p>
            </div>
          </div>
          <Badge variant={platform.is_verified ? 'success' : 'secondary'}>
            {platform.is_verified ? (
              <><CheckCircle className="h-3 w-3 mr-1" /> Verified</>
            ) : (
              <><XCircle className="h-3 w-3 mr-1" /> Pending</>
            )}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {platform.last_synced_at && (
            <p className="text-xs text-muted-foreground">
              Last synced: {format(new Date(platform.last_synced_at), 'PPp')}
            </p>
          )}
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              className="flex-1"
              onClick={() => onSync(platform.id)}
              disabled={isLoading}
            >
              <RefreshCw className={cn('h-4 w-4 mr-2', isLoading && 'animate-spin')} />
              Sync Now
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => onDisconnect(platform.id)}
              disabled={isLoading}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
