export default function MacroBar({ current = 0, target = 100, label, color = '#3b82f6', unit = 'g' }) {
  const percent = target > 0 ? Math.min(100, (current / target) * 100) : 0

  return (
    <div className="mb-2.5">
      <div className="flex justify-between text-xs text-text-secondary mb-1">
        <span className="font-medium">{label}</span>
        <span className="font-semibold">{Math.round(current)}/{target}{unit}</span>
      </div>
      <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${percent}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}
