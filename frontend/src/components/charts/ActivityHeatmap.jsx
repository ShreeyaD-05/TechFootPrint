import { useMemo } from 'react'

// Hoisted — must be defined before useMemo references them
const getLevel = (count) => {
  if (count === 0) return 0
  if (count <= 2) return 1
  if (count <= 5) return 2
  if (count <= 10) return 3
  return 4
}

const LEVEL_COLORS = [
  'bg-gray-100 dark:bg-gray-800',
  'bg-green-200 dark:bg-green-900',
  'bg-green-400 dark:bg-green-700',
  'bg-green-600 dark:bg-green-500',
  'bg-green-800 dark:bg-green-300',
]

export default function ActivityHeatmap({ data, days = 365 }) {
  const heatmapData = useMemo(() => {
    // Guard: data must be a plain object {dateStr: count}
    const safeData = (data && typeof data === 'object' && !Array.isArray(data)) ? data : {}

    const today = new Date()
    const startDate = new Date(today)
    startDate.setDate(startDate.getDate() - days)

    const weeks = []
    let currentWeek = []
    let currentDate = new Date(startDate)

    // Pad to start on Sunday
    const startDay = currentDate.getDay()
    for (let i = 0; i < startDay; i++) {
      currentWeek.push(null)
    }

    while (currentDate <= today) {
      const dateStr = currentDate.toISOString().split('T')[0]
      const count = safeData[dateStr] || 0

      currentWeek.push({
        date: new Date(currentDate),
        count,
        level: getLevel(count),
      })

      if (currentDate.getDay() === 6) {
        weeks.push(currentWeek)
        currentWeek = []
      }

      currentDate.setDate(currentDate.getDate() + 1)
    }

    if (currentWeek.length > 0) {
      weeks.push(currentWeek)
    }

    return weeks
  }, [data, days])

  return (
    <div className="space-y-2">
      <div className="flex gap-1 overflow-x-auto pb-2">
        {heatmapData.map((week, weekIndex) => (
          <div key={weekIndex} className="flex flex-col gap-1">
            {week.map((day, dayIndex) => (
              <div
                key={dayIndex}
                className={`w-3 h-3 rounded-sm ${
                  day ? LEVEL_COLORS[day.level] : 'bg-transparent'
                }`}
                title={day ? `${day.date.toLocaleDateString()}: ${day.count} activities` : ''}
              />
            ))}
          </div>
        ))}
      </div>
      
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>Less</span>
        <div className="flex gap-1">
          {[0, 1, 2, 3, 4].map((level) => (
            <div
              key={level}
              className={`w-3 h-3 rounded-sm ${LEVEL_COLORS[level]}`}
            />
          ))}
        </div>
        <span>More</span>
      </div>
    </div>
  )
}
