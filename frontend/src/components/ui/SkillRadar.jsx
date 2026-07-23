import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, ResponsiveContainer, Tooltip
} from 'recharts'

export default function SkillRadar({ data = [], loading = false }) {
  if (loading) {
    return <div className="h-64 bg-secondary rounded-xl animate-pulse" />
  }

  if (!data.length) {
    return (
      <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">
        Solve more problems to see your skill radar
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
        <PolarGrid stroke="hsl(var(--border))" />
        <PolarAngleAxis
          dataKey="topic"
          tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }}
          tickCount={4}
        />
        <Radar
          name="Skill"
          dataKey="score"
          stroke="hsl(var(--primary))"
          fill="hsl(var(--primary))"
          fillOpacity={0.25}
          strokeWidth={2}
        />
        <Tooltip
          formatter={(v) => [`${v}/100`, 'Proficiency']}
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
            fontSize: '12px',
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
