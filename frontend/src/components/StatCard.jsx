import { Card, CardContent } from './ui/Card'
import { cn } from '@/utils/cn'

export function StatCard({ title, value, icon: Icon, trend, className }) {
  return (
    <Card className={cn('hover:shadow-md transition-shadow', className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold">{value}</p>
            {trend && (
              <p className={cn(
                'text-xs font-medium',
                trend > 0 ? 'text-green-600' : 'text-red-600'
              )}>
                {trend > 0 ? '+' : ''}{trend}% from last week
              </p>
            )}
          </div>
          {Icon && (
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Icon className="h-6 w-6 text-primary" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
